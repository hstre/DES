"""
OpenRouter API client. Reads OPENROUTER_API_KEY from environment — never from code.
Timeout: 120s. Max retries: 2. Backoff: 4s, 8s.
"""

import os
import time
import json
import urllib.request
import urllib.error
from typing import Any

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT_SECONDS = 120
MAX_RETRIES = 2
BACKOFF_SECONDS = [4, 8]


class OpenRouterError(Exception):
    def __init__(self, error_type: str, detail: str, http_status: int | None = None):
        super().__init__(detail)
        self.error_type = error_type
        self.detail = detail
        self.http_status = http_status


def _get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise OpenRouterError(
            "missing_field",
            "OPENROUTER_API_KEY environment variable is not set.",
        )
    return key


def call_model(
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 256,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Returns dict with keys: response_text, prompt_tokens, completion_tokens,
    latency_ms, http_status, error, error_detail.

    On dry_run=True, skips the actual HTTP request and returns a stub response.
    """
    if dry_run:
        return {
            "response_text": "[DRY RUN — no API call made]",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "latency_ms": 0,
            "http_status": 200,
            "error": None,
            "error_detail": None,
        }

    api_key = _get_api_key()

    payload = json.dumps({
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/hstre/des",
        "X-Title": "DES-Benchmark",
    }

    req = urllib.request.Request(
        OPENROUTER_API_URL,
        data=payload,
        headers=headers,
        method="POST",
    )

    last_error: OpenRouterError | None = None

    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            time.sleep(BACKOFF_SECONDS[attempt - 1])

        t_start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                latency_ms = int((time.monotonic() - t_start) * 1000)
                http_status = resp.status
                raw_body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            latency_ms = int((time.monotonic() - t_start) * 1000)
            http_status = exc.code
            try:
                body = exc.read().decode("utf-8")
            except Exception:
                body = str(exc)
            if 400 <= http_status < 500:
                last_error = OpenRouterError(
                    "http_error_4xx",
                    f"HTTP {http_status}: {body}",
                    http_status=http_status,
                )
                break  # 4xx errors are not retriable
            else:
                last_error = OpenRouterError(
                    "http_error_5xx",
                    f"HTTP {http_status}: {body}",
                    http_status=http_status,
                )
            continue
        except TimeoutError:
            latency_ms = int((time.monotonic() - t_start) * 1000)
            last_error = OpenRouterError(
                "network_timeout",
                f"Request timed out after {TIMEOUT_SECONDS}s (attempt {attempt + 1})",
            )
            continue
        except OSError as exc:
            latency_ms = int((time.monotonic() - t_start) * 1000)
            last_error = OpenRouterError(
                "network_timeout",
                f"Network error: {exc} (attempt {attempt + 1})",
            )
            continue

        # Parse JSON response
        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            last_error = OpenRouterError(
                "json_decode_error",
                f"JSON parse failed: {exc}. Body: {raw_body[:200]}",
                http_status=http_status,
            )
            break  # malformed response is not retriable

        try:
            response_text = data["choices"][0]["message"]["content"].strip()
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
        except (KeyError, IndexError, TypeError) as exc:
            last_error = OpenRouterError(
                "missing_field",
                f"Unexpected response structure: {exc}. Keys: {list(data.keys())}",
                http_status=http_status,
            )
            break

        return {
            "response_text": response_text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency_ms": latency_ms,
            "http_status": http_status,
            "error": None,
            "error_detail": None,
        }

    # All attempts exhausted or non-retriable error
    assert last_error is not None
    return {
        "response_text": "",
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "latency_ms": latency_ms,
        "http_status": last_error.http_status,
        "error": last_error.error_type,
        "error_detail": last_error.detail,
    }

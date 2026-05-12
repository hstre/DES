"""
OpenRouter API client. OPENROUTER_API_KEY from environment only — never hardcoded.
Timeout: 120s. Retries: 2. Backoff: 4s, 8s.
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

SYSTEM_PROMPT = "You are a precise and honest research assistant."


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


def _classify_http_error(status: int, body: str) -> str:
    if status == 429:
        return "rate_limit"
    if status == 400 and ("model" in body.lower() or "invalid" in body.lower()):
        return "invalid_model"
    if status in (503, 502) and "provider" in body.lower():
        return "provider_error"
    if status == 404:
        return "invalid_model"
    if 400 <= status < 500:
        return "http_error_4xx"
    return "http_error_5xx"


def call_model(
    model_id: str,
    prompt: str,
    max_tokens: int = 1024,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Returns dict with keys matching the nested runs.jsonl schema:
      response_text, finish_reason, raw,
      prompt_tokens, completion_tokens, total_tokens, cost_usd,
      latency_ms, http_status, error_type, error_detail.

    error_type is None on success.
    On dry_run=True, returns stub with no HTTP call.
    """
    if dry_run:
        return {
            "response_text": "[DRY RUN — no API call made]",
            "finish_reason": "dry_run",
            "raw": {},
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cost_usd": None,
            "latency_ms": 0,
            "http_status": 200,
            "error_type": None,
            "error_detail": None,
        }

    api_key = _get_api_key()

    payload = json.dumps({
        "model": model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
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
    latency_ms = 0

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
            err_type = _classify_http_error(http_status, body)
            last_error = OpenRouterError(err_type, f"HTTP {http_status}: {body}", http_status=http_status)
            if err_type in ("rate_limit", "http_error_5xx", "provider_error"):
                continue
            break
        except TimeoutError:
            latency_ms = int((time.monotonic() - t_start) * 1000)
            last_error = OpenRouterError(
                "network_timeout",
                f"Timed out after {TIMEOUT_SECONDS}s (attempt {attempt + 1})",
            )
            continue
        except OSError as exc:
            latency_ms = int((time.monotonic() - t_start) * 1000)
            last_error = OpenRouterError(
                "network_timeout",
                f"Network error: {exc} (attempt {attempt + 1})",
            )
            continue

        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            last_error = OpenRouterError(
                "json_decode_error",
                f"JSON parse failed: {exc}. Body prefix: {raw_body[:200]}",
                http_status=http_status,
            )
            break

        try:
            choice = data["choices"][0]
            response_text = choice["message"]["content"].strip()
            finish_reason = choice.get("finish_reason")
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens")
            completion_tokens = usage.get("completion_tokens")
            total_tokens = usage.get("total_tokens")
            cost_usd = usage.get("cost")
        except (KeyError, IndexError, TypeError) as exc:
            last_error = OpenRouterError(
                "malformed_response",
                f"Unexpected structure: {exc}. Keys: {list(data.keys())}",
                http_status=http_status,
            )
            break

        return {
            "response_text": response_text,
            "finish_reason": finish_reason,
            "raw": data,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
            "http_status": http_status,
            "error_type": None,
            "error_detail": None,
        }

    assert last_error is not None
    return {
        "response_text": "",
        "finish_reason": None,
        "raw": {},
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "cost_usd": None,
        "latency_ms": latency_ms,
        "http_status": last_error.http_status,
        "error_type": last_error.error_type,
        "error_detail": last_error.detail,
    }

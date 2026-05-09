"""
des_premium/run_cot_cond.py
CoT runner for cheap and premium model tiers.
Single-shot COT_PROMPT_TEMPLATE call per domain/seed.
"""

import json
import os
import re
import sys
import time
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from des_premium.config import CHEAP_CONFIG, PREMIUM_CONFIG, DOMAINS, SEEDS, COT_PROMPT_TEMPLATE

_clients: dict = {}


def _init_cot_clients() -> None:
    global _clients
    dk = os.environ.get("DEEPSEEK_API_KEY", "")
    ok = os.environ.get("OPENROUTER_API_KEY", "")
    if not dk:
        raise EnvironmentError("DEEPSEEK_API_KEY must be set.")
    _clients["deepseek"] = OpenAI(
        api_key=dk,
        base_url="https://api.deepseek.com/v1",
    )
    if ok:
        _clients["openrouter"] = OpenAI(
            api_key=ok,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/hstre/DES",
                "X-Title": "DES-premium",
            },
        )


def _call_cot(model: str, provider: str, prompt: str,
              max_tokens: int = 2000) -> tuple[str, dict]:
    """
    Call model with CoT prompt. Returns (content, usage_dict).
    Captures reasoning_content for DeepSeek-R1 if available.
    """
    client = _clients.get(provider)
    if client is None:
        raise RuntimeError(f"Client for provider '{provider}' not initialised.")

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=max_tokens,
    )

    content  = resp.choices[0].message.content or ""
    # R1-specific reasoning field (may not exist on all SDKs)
    reasoning = getattr(resp.choices[0].message, "reasoning_content", None) or ""

    usage = {}
    if resp.usage:
        usage = {
            "prompt_tokens":     resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "total_tokens":      resp.usage.total_tokens,
        }
        # R1 reasoning tokens (deepseek-reasoner returns completion_tokens_details)
        if hasattr(resp.usage, "completion_tokens_details") and resp.usage.completion_tokens_details:
            d = resp.usage.completion_tokens_details
            usage["reasoning_tokens"] = getattr(d, "reasoning_tokens", None)

    return content, reasoning, usage


# ── CoT output parsing ────────────────────────────────────────────────────────

def _count_reasoning_steps(text: str) -> int:
    """Count numbered steps or distinct paragraphs as proxy for reasoning depth."""
    numbered = len(re.findall(r"^\s*\d+[\.\)]\s", text, re.MULTILINE))
    if numbered >= 2:
        return numbered
    # Fall back: non-empty paragraphs
    return len([p for p in text.split("\n\n") if p.strip()])


def _extract_claim_sentences(text: str) -> list[str]:
    """Split CoT text into sentence-level claim units."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def _token_overlap(a: str, b: str) -> float:
    STOP = {"the","a","an","is","are","was","were","of","in","to","for","and","or",
            "but","not","with","by","from","that","this","it","be","as","at"}
    ta = set(re.sub(r"[^a-z0-9 ]", "", a.lower()).split()) - STOP
    tb = set(re.sub(r"[^a-z0-9 ]", "", b.lower()).split()) - STOP
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def _semantic_duplication_rate(sentences: list[str]) -> float:
    if len(sentences) < 2:
        return 0.0
    count = 0
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            if _token_overlap(sentences[i], sentences[j]) > 0.70:
                count += 1
                break
    return round(count / max(len(sentences), 1), 4)


_FALSE_PROOF_PATTERNS_M01 = [
    r"T\(n\)\s*always\s*(converges|terminates|reaches\s*1)",
    r"all\s*(trajectories|sequences)\s*(converge|terminate)",
    r"no\s*(divergent|infinite)\s*(trajectory|sequence)",
    r"proven\s*to\s*(converge|terminate)",
]

def _false_proof_scan_m01(text: str) -> dict:
    """Scan CoT output for M01 false proof language."""
    errors = [p for p in _FALSE_PROOF_PATTERNS_M01
              if re.search(p, text, re.IGNORECASE)]
    return {
        "false_proof_detected": len(errors) > 0,
        "false_proof_count":    len(errors),
        "patterns_matched":     errors,
    }


# ── Main runner ───────────────────────────────────────────────────────────────

def run_cot_condition(
    domain_id:   str,
    seed_n:      int,
    config:      dict,
    results_dir: Path,
) -> dict:
    """Run single-shot CoT for one domain/seed/config."""
    run_dir     = results_dir / f"{domain_id}_seed{seed_n}"
    run_dir.mkdir(parents=True, exist_ok=True)
    result_file = run_dir / "outcome.json"

    if result_file.exists():
        print(f"  [skip] {domain_id} seed={seed_n}")
        with open(result_file) as f:
            return json.load(f)

    seed_question = DOMAINS[domain_id]
    tier          = config["tier"]
    model         = config["builder_model"]
    provider      = config["builder_provider"]

    print(f"  {domain_id} [CoT-{tier} | seed{seed_n}] model={model}")

    random.seed(seed_n)
    prompt = COT_PROMPT_TEMPLATE.format(seed_question=seed_question, seed_n=seed_n)

    t_start = time.time()
    try:
        content, reasoning, usage = _call_cot(model, provider, prompt)
    except Exception as e:
        print(f"  ERROR: {e}")
        content, reasoning, usage = "", "", {}

    # deepseek-reasoner returns answer in reasoning_content when content is empty
    if not content and reasoning:
        content  = reasoning
        reasoning = ""

    elapsed   = round(time.time() - t_start, 1)
    sentences = _extract_claim_sentences(content)
    dup_rate  = _semantic_duplication_rate(sentences)
    steps     = _count_reasoning_steps(content)

    fp_info = None
    if domain_id == "M01":
        fp_info = _false_proof_scan_m01(content + " " + reasoning)

    data = {
        "domain_id":                  domain_id,
        "seed":                       seed_n,
        "config":                     {k: v for k, v in config.items() if k != "note"},
        "outcome":                    "COT_COMPLETE" if content else "COT_ERROR",
        "word_count":                 len(content.split()),
        "reasoning_steps":            steps,
        "sentence_count":             len(sentences),
        "semantic_duplication_rate":  dup_rate,
        "reasoning_word_count":       len(reasoning.split()) if reasoning else 0,
        "false_proof_info":           fp_info,
        "false_proof_detected":       fp_info["false_proof_detected"] if fp_info else None,
        "elapsed_seconds":            elapsed,
        "token_usage":                usage,
        "output":                     content,
        "reasoning_content":          reasoning if reasoning else None,
    }

    with open(result_file, "w") as f:
        json.dump(data, f, indent=2)

    fp = f" fp={fp_info['false_proof_count']}" if fp_info else ""
    print(f"  {domain_id}/CoT-{tier}/seed{seed_n}: {steps} steps "
          f"| {len(sentences)} sentences | dup={dup_rate} | {elapsed}s{fp}")
    return data


def run_cot_batch(config: dict, results_dir: Path, domains: list | None = None) -> list:
    """Run all domain×seed combinations for one config."""
    _init_cot_clients()
    results_dir.mkdir(parents=True, exist_ok=True)
    use_domains = domains or list(DOMAINS.keys())
    results = []
    for domain_id in use_domains:
        for seed_n in SEEDS:
            r = run_cot_condition(domain_id, seed_n, config, results_dir)
            results.append(r)
    return results

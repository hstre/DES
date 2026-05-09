"""
des_premium/config.py
Model configs and domain definitions for 2×2 model-architecture matrix.
"""

CHEAP_CONFIG = {
    "builder_model":    "deepseek-chat",
    "builder_provider": "deepseek",
    "falsifier_model":  "openai/gpt-4o",
    "falsifier_provider": "openrouter",
    "tier": "cheap",
}

# Pre-registered choice: Option A — DeepSeek-R1, falsifier held constant.
PREMIUM_CONFIG = {
    "builder_model":    "deepseek-reasoner",
    "builder_provider": "deepseek",
    "falsifier_model":  "openai/gpt-4o",
    "falsifier_provider": "openrouter",
    "tier": "premium",
    "note": "Option A: DeepSeek-R1 builder, same GPT-4o falsifier as cheap config",
}

DOMAINS = {
    "R01": "Does raising the minimum wage increase unemployment?",
    "R04": "Is GDP a valid proxy for human wellbeing?",
    "R05": "Is intermittent fasting effective for long-term weight loss?",
    "M01": (
        "Investigate the long-term behavior of T(n): "
        "if n mod 3 = 0: T(n) = n/3, "
        "if n mod 3 = 1: T(n) = 4n+2, "
        "if n mod 3 = 2: T(n) = 2n-1. "
        "Identify cycles, divergence patterns, invariants, and plausible conjectures."
    ),
    "N03": "Is artificial general intelligence achievable within 20 years?",
}

# Pilot: M01+N03 only (R01/R04/R05 lack seeded cheap DES baselines from Papers 4-8)
PILOT_DOMAINS = ["M01", "N03"]

SEEDS = [101, 202, 303]

COT_PROMPT_TEMPLATE = """{seed_question}

Please think through this carefully step by step. Consider:
1. The strongest evidence on each side
2. Key uncertainties and what would resolve them
3. The most defensible conclusion given available evidence

Provide a structured analysis with your reasoning visible.

# run_seed: {seed_n}"""


# ── Phase B (Review) Configuration ───────────────────────────────────────────

REVIEW_CONFIG = {
    "reviewer_model":       "google/gemini-3.1-pro-preview",
    "reviewer_provider":    "openrouter",
    "reviewer_temperature": 0.2,
    "reviewer_max_tokens":  4000,
    "graph_serialization_format": "json",
    "include_spl_metadata": True,
    "note": "Phase B reviewer; gemini-3.1-pro-preview = non-reasoning-RL premium model.",
}

PHASE_B_VARIANTS = {
    "LOOP_COMPLETE":            "standard_review",
    "SEMANTIC_DUPLICATION":     "premature_review",
    "MAX_LOOPS_REACHED":        "unsaturated_review",
    "CONTRADICTION_UNRESOLVED": "contradiction_review",
}

# ── Judge Configuration ───────────────────────────────────────────────────────

JUDGE_CONFIG = {
    "judge_model":       "anthropic/claude-opus-4.7",
    "judge_provider":    "openrouter",
    "judge_temperature": 0.1,
    "judge_max_tokens":  2000,
    "note": "External judge; must not be same model as Reviewer.",
}

# ── COT Premium config (Phase B reviewer model used as single-shot CoT) ──────

COT_PREMIUM_CONFIG = {
    "builder_model":    "google/gemini-3.1-pro-preview",
    "builder_provider": "openrouter",
    "tier": "cot_premium_pb",
    "note": "COT_PREMIUM condition: same reviewer model as Phase B, single-shot.",
}

# Pilot: same scope as 2x2 matrix
PILOT_DOMAINS = ["M01", "N03"]

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
"""

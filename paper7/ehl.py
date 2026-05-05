"""
paper7/ehl.py
Epistemic Half-Life: claim weight decay wrapper.
Does NOT modify DES internals or state confidence values.
Decay affects claim selection weight only.
WP2 (Rentschler 2026).
"""
import random
import math


class EpistemicHalfLife:
    def __init__(self, decay_factor: float = 0.90):
        assert 0.50 <= decay_factor <= 1.00, f"decay_factor must be in [0.50, 1.00], got {decay_factor}"
        self.decay = decay_factor
        self.claim_ages: dict = {}   # cid -> loop sealed
        self._last_seed: int | None = None
        self._using_fallback_age: bool = False
        self._fallback_cids: list = []

    def age_claims(self, claims: dict, current_loop: int) -> dict:
        """
        weight = decay ^ (current_loop - seal_loop)
        Uses claim["sealed_at_loop"] if available; falls back to wrapper-map
        (first seen = current_loop). Fallback is logged via _fallback_cids.
        """
        weights = {}
        for cid, claim in claims.items():
            if cid not in self.claim_ages:
                if "sealed_at_loop" in claim:
                    self.claim_ages[cid] = claim["sealed_at_loop"]
                else:
                    self.claim_ages[cid] = current_loop
                    self._using_fallback_age = True
                    self._fallback_cids.append(cid)
            age = max(0, current_loop - self.claim_ages[cid])
            weights[cid] = self.decay ** age
        return weights

    def weighted_select(self, claims: dict, current_loop: int,
                        criterion) -> list:
        """
        Select claims weighted by age decay.
        Seeded for reproducibility — seed logged in _last_seed.
        Returns list of (cid, claim) tuples, up to k=3.
        """
        weights = self.age_claims(claims, current_loop)
        candidates = [(cid, c) for cid, c in claims.items()
                      if criterion(c) and weights.get(cid, 1.0) > 0.01]
        if not candidates:
            return []
        seed = abs(hash(str(sorted(claims.keys())) + str(current_loop))) % (2 ** 31)
        rng = random.Random(seed)
        self._last_seed = seed
        w_vals = [weights[cid] for cid, _ in candidates]
        total = sum(w_vals)
        if total == 0:
            return []
        probs = [w / total for w in w_vals]
        return rng.choices(candidates, weights=probs, k=min(3, len(candidates)))

    def check_odc(self, loop_metrics: list) -> bool:
        """
        Over-Decay Collapse guard. Only relevant for decay < 0.85.
        Fires when 3 consecutive loops show novel_claims=0 and dup_rate > 0.50.
        """
        if self.decay >= 0.85:
            return False
        if len(loop_metrics) < 3:
            return False
        last3 = loop_metrics[-3:]
        novel_dropping = all(m.get("novel_claims", 1) == 0 for m in last3)
        dup_rising = last3[-1].get("semantic_duplication_rate", 0) > 0.50
        return novel_dropping and dup_rising

    def loop_snapshot(self, claims: dict, current_loop: int) -> dict:
        """Return per-loop EHL diagnostics for ehl_log.json."""
        weights = self.age_claims(claims, current_loop)
        ages = {cid: current_loop - self.claim_ages.get(cid, current_loop)
                for cid in claims}
        avg_age = sum(ages.values()) / max(len(ages), 1)
        avg_weight = sum(weights.values()) / max(len(weights), 1)
        return {
            "loop": current_loop,
            "decay_factor": self.decay,
            "n_claims": len(claims),
            "avg_claim_age": round(avg_age, 2),
            "avg_weight": round(avg_weight, 4),
            "min_weight": round(min(weights.values(), default=0.0), 4),
            "last_seed": self._last_seed,
            "fallback_age_used": self._using_fallback_age,
            "fallback_cids": list(self._fallback_cids),
        }

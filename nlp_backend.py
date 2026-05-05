"""
nlp_backend.py — SentenceTransformer-based SPL backend.
Maps natural language into probability simplex Π over relational types ℛ.
WP2 (Rentschler 2026). Do not modify after initial creation.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict

try:
    from sentence_transformers import SentenceTransformer
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False

# Relational basis ℛ — 10 types forming the simplex
RELATION_TYPES = [
    "causal",
    "conditional",
    "comparative",
    "correlational",
    "temporal",
    "definitional",
    "evidential",
    "contrastive",
    "normative",
    "mechanistic",
]

# Prototype phrases anchoring each relation type in embedding space
RELATION_PROTOTYPES = {
    "causal": (
        "causes leads to produces results in increases decreases drives "
        "effect impact outcome consequence"
    ),
    "conditional": (
        "if only when under conditions contingent upon unless given that "
        "assuming depends on requires"
    ),
    "comparative": (
        "better than worse than more effective than compared to superior "
        "inferior outperforms relative to"
    ),
    "correlational": (
        "associated with correlated with related to predicts linked to "
        "connection relationship co-occurs"
    ),
    "temporal": (
        "over time historically in the long run precedes follows duration "
        "period change trend evolution"
    ),
    "definitional": (
        "is defined as means characterized by what is consists of refers to "
        "constitutes represents"
    ),
    "evidential": (
        "evidence shows data supports studies find research indicates "
        "demonstrates confirms suggests"
    ),
    "contrastive": (
        "however despite contradicts fails undermines challenges refutes "
        "weakens alternative contrary"
    ),
    "normative": (
        "should ought policy requires justified ethical recommended must "
        "necessary desirable appropriate"
    ),
    "mechanistic": (
        "mechanism pathway how does via process through which mediates "
        "explains operates functions"
    ),
}


@dataclass
class Projection:
    P_r: Dict[str, float]
    text: str


class SPLNLPBackend:
    """
    Semantic Projection Layer NLP Backend.
    Projects text into probability simplex Π over RELATION_TYPES.
    Uses cosine similarity to prototype embeddings + softmax.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2",
                 builder_origin: str = "alpha"):
        if not _ST_AVAILABLE:
            raise ImportError(
                "sentence-transformers required: "
                "pip install sentence-transformers --break-system-packages"
            )
        self._model = SentenceTransformer(model_name)
        self._builder_origin = builder_origin
        self._temperature = 5.0

        protos = [RELATION_PROTOTYPES[r] for r in RELATION_TYPES]
        self._proto_embs = self._model.encode(protos, normalize_embeddings=True)

    def project_text(self, text: str) -> Projection:
        emb = self._model.encode([text], normalize_embeddings=True)[0]
        sims = self._proto_embs @ emb
        shifted = sims - sims.max()
        exp_s = np.exp(self._temperature * shifted)
        total = exp_s.sum()
        P_r = {
            RELATION_TYPES[i]: float(exp_s[i] / total)
            for i in range(len(RELATION_TYPES))
        }
        return Projection(P_r=P_r, text=text)

"""
Pre-registered classification algorithm for Paper 3.
Version: 1.0 -- FROZEN 4. Mai 2026
DO NOT MODIFY thresholds or rules.
Any change requires explicit versioning.

v1.1 -- post-null revision, 2026-05-04
"""

ALGORITHM_VERSION = "1.1"
ALGORITHM_DATE = "2026-05-04"
ALGORITHM_CHANGE = "Removed generated_by trigger; added contradicted+no-evidence and conf<0.25"


def is_anomalous(claim: dict) -> bool:
    """
    v1.1 -- documented post-null revision.
    v1.0 produced 100% unclassified because generated_by trigger
    flagged healthy Anti-Delphi claims. role-generated != pathological.
    """
    conf = claim.get("confidence", 1.0)
    modality = claim.get("modality", "")
    status = claim.get("status", "")
    scope = claim.get("scope", {})
    evidence = claim.get("evidence_refs", [])

    if conf < 0.35 and modality == "hypothesis":
        return True
    if status == "underspecified" and scope == {}:
        return True
    if status == "contradicted" and len(evidence) == 0:
        return True
    if conf < 0.25 and status not in {"supported", "established"}:
        return True
    return False
    # generated_by condition removed -- role tags are not anomalies


def scope_shifted(claim: dict, root_claim: dict) -> bool:
    root_domain = root_claim.get("scope", {}).get("domain", None)
    claim_domain = claim.get("scope", {}).get("domain", None)
    if root_domain is None or claim_domain is None:
        return False
    return root_domain.lower() != claim_domain.lower()


def introduces_new_frame(claim: dict, root_claim: dict) -> bool:
    root_tokens = set(
        (root_claim.get("subject", "") + " " +
         root_claim.get("predicate", "") + " " +
         root_claim.get("object", "")).lower().split()
    )
    claim_tokens = set(
        (claim.get("subject", "") + " " +
         claim.get("object", "")).lower().split()
    )
    stop = {"the","a","an","is","are","was","were","of","in","to","for",
            "and","or","but","not","with","by","from","that","this","it"}
    root_tokens -= stop
    claim_tokens -= stop
    if not root_tokens or not claim_tokens:
        return False
    overlap = len(root_tokens & claim_tokens) / len(claim_tokens)
    return overlap < 0.3


def classify(claim: dict, root_claim: dict) -> str:
    """
    Pre-registered classification. Priority: 1 > 4 > 3 > 2.
    Category 4 intentionally prioritizes sensitivity over specificity.
    Returns: "1", "2", "3", "4", or "unclassified"
    """
    history = claim.get("history", [])
    status = claim.get("status", "")
    conf = claim.get("confidence", 0)
    evidence = claim.get("evidence_refs", [])
    branch_open = claim.get("branch_open", False)
    sealed = claim.get("sealed", False)
    is_synth = claim.get("is_synthesis", False)
    scope = claim.get("scope", {})

    # Priority 1: Genuine Hallucination
    if (status == "contradicted"
            and not branch_open
            and len(evidence) == 0
            and conf < 0.3
            and "T9" not in history):
        return "1"

    # Priority 2: Early Reframing (before cross-domain)
    if (is_synth
            and status == "supported"
            and conf >= 0.5
            and "T9" in history
            and not branch_open):
        return "4"
    if (status == "supported"
            and conf >= 0.6
            and "T9" in history
            and len(evidence) > 0
            and introduces_new_frame(claim, root_claim)):
        return "4"

    # Priority 3: Cross-Domain Projection
    if (status == "supported"
            and len(evidence) > 0
            and conf >= 0.5
            and scope != {}
            and "T4" in history
            and not is_synth
            and scope_shifted(claim, root_claim)):
        return "3"

    # Priority 4: Weak Hypothesis
    if (status in {"hypothesis", "disputed"}
            and 0.2 <= conf < 0.5
            and len(evidence) == 0
            and not sealed
            and "T1" not in history):
        return "2"

    return "unclassified"

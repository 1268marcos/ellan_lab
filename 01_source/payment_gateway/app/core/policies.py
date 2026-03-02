from __future__ import annotations

from typing import Any, Dict, List

from app.core.hashing import canonical_json, sha256_prefixed


def _policy_hash(policy: Dict[str, Any]) -> str:
    # hash estável para auditoria / cache
    return sha256_prefixed(canonical_json(policy))


def list_policies() -> List[Dict[str, Any]]:
    """
    Fonte única das policies.
    (No futuro você pode versionar/armazenar em DB ou arquivo.)
    """
    policies = [
        {
            "policy_id": "risk_sp_default_v3",
            "region": "SP",
            "version": "3",
            "thresholds": {"allow_max": 39, "challenge_min": 40, "block_min": 70},
            "notes": "Default SP v3 (determinística)",
        },
        {
            "policy_id": "risk_pt_default_v3",
            "region": "PT",
            "version": "3",
            "thresholds": {"allow_max": 39, "challenge_min": 40, "block_min": 70},
            "notes": "Default PT v3 (determinística)",
        },
    ]

    # acrescenta hash para auditoria
    for p in policies:
        p["policy_hash"] = _policy_hash(p)

    return policies


def get_policy_by_region(region: str) -> Dict[str, Any]:
    reg = (region or "").upper()
    for p in list_policies():
        if p["region"] == reg:
            return p

    # fallback seguro
    p = {
        "policy_id": "risk_default_v3",
        "region": reg or "XX",
        "version": "3",
        "thresholds": {"allow_max": 39, "challenge_min": 40, "block_min": 70},
        "notes": "Fallback policy",
    }
    p["policy_hash"] = _policy_hash(p)
    return p
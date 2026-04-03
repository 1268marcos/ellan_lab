# 01_source/payment_gateway/app/services/antifraud_service.py
# 02/04/2026

from typing import Any, Dict, Optional

from app.core.risk_engine import evaluate_risk


def check_antifraud(
    *,
    regiao: str,
    canal: str,
    metodo: str,
    valor: float,
    porta: int,
    payment_interface: Optional[str] = None,
    device_known: bool = False,
    velocity: Optional[Dict[str, int]] = None,
    anti_replay_status: str = "ok",
    ip_hash: str = "",
    device_hash: str = "",
    integration_status: str = "ACTIVE",
) -> Dict[str, Any]:
    velocity = velocity or {}

    risk_result = evaluate_risk(
        region=regiao,
        canal=canal,
        metodo=metodo,
        valor=valor,
        porta=porta,
        payment_interface=payment_interface,
        device_known=device_known,
        velocity=velocity,
        anti_replay_status=anti_replay_status,
        ip_hash=ip_hash,
        device_hash=device_hash,
        integration_status=integration_status,
    )

    decision = risk_result["decision"]
    reasons = risk_result.get("reasons", [])

    if decision == "ALLOW":
        approved = True
        reason = "ok"
    elif decision == "CHALLENGE":
        approved = False
        reason = "challenge_required"
    else:
        approved = False
        reason = reasons[0]["code"].lower() if reasons else "blocked"

    return {
        "approved": approved,
        "reason": reason,
        "decision": decision,
        "score": risk_result["score"],
        "reasons": reasons,
        "signals": risk_result.get("signals", {}),
        "policy": risk_result.get("policy", {}),
    }
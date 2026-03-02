from typing import Any, Dict, List, Literal, Tuple
from app.core.policies import get_policy_by_region

Decision = Literal["ALLOW", "CHALLENGE", "BLOCK"]


# Foi substituído por ser interno hardcoded
# def get_policy(region: str) -> Dict[str, Any]:
#     region = (region or "").upper()
#    if region == "PT":
#        return {
#             "policy_id": "risk_pt_default_v3",
#             "thresholds": {"allow_max": 39, "challenge_min": 40, "block_min": 70},
#         }
#     return {
#         "policy_id": "risk_sp_default_v3",
#         "thresholds": {"allow_max": 39, "challenge_min": 40, "block_min": 70},
#     }


def evaluate_risk(
    *,
    region: str,
    metodo: str,
    valor: float,
    porta: int,
    device_known: bool,
    velocity: Dict[str, int],
    anti_replay_status: str,
    ip_hash: str,
    device_hash: str,
) -> Dict[str, Any]:
    """
    Regras v1 determinísticas (sem random):
      - payload_mismatch => BLOCK pesado
      - device novo aumenta score
      - velocity alta aumenta score
      - valor alto aumenta score
      - cartão aumenta score
    """
    metodo_u = (metodo or "").upper()
    # policy = get_policy(region)
    policy = get_policy_by_region(region)
    thresholds = policy["thresholds"]

    score = 0
    reasons: List[Dict[str, Any]] = []

    # Hard blocks
    if anti_replay_status == "payload_mismatch":
        score += 90
        reasons.append({"code": "IDEMPOTENCY_PAYLOAD_MISMATCH", "weight": 90, "detail": "Idempotency-Key reutilizada com payload diferente"})

    # Basic validation-ish
    if porta < 1 or porta > 24:
        score += 80
        reasons.append({"code": "PORTA_OUT_OF_RANGE", "weight": 80, "detail": "Porta fora do range permitido"})

    # Device signal
    if not device_known:
        score += 15
        reasons.append({"code": "DEVICE_NEW", "weight": 15, "detail": "Primeira vez deste dispositivo"})
    else:
        score -= 5
        reasons.append({"code": "DEVICE_KNOWN", "weight": -5, "detail": "Dispositivo já visto"})

    # Payment method
    if metodo_u in ["CARTAO", "CARD"]:
        score += 10
        reasons.append({"code": "PAYMENT_METHOD_CARD", "weight": 10, "detail": "Método cartão exige cautela"})

    # Value
    if valor >= 500:
        score += 20
        reasons.append({"code": "HIGH_VALUE", "weight": 20, "detail": "Valor alto"})
    elif valor >= 200:
        score += 8
        reasons.append({"code": "MID_VALUE", "weight": 8, "detail": "Valor acima do padrão"})

    # Velocity
    ip_5m = int(velocity.get("ip_5m", 0))
    dev_5m = int(velocity.get("device_5m", 0))
    porta_5m = int(velocity.get("porta_5m", 0))

    if ip_5m >= 15:
        score += 25
        reasons.append({"code": "VELOCITY_IP_SPIKE", "weight": 25, "detail": f"ip_5m={ip_5m}"})
    elif ip_5m >= 8:
        score += 12
        reasons.append({"code": "VELOCITY_IP_ELEVATED", "weight": 12, "detail": f"ip_5m={ip_5m}"})

    if dev_5m >= 10:
        score += 18
        reasons.append({"code": "VELOCITY_DEVICE_SPIKE", "weight": 18, "detail": f"device_5m={dev_5m}"})
    elif dev_5m >= 6:
        score += 10
        reasons.append({"code": "VELOCITY_DEVICE_ELEVATED", "weight": 10, "detail": f"device_5m={dev_5m}"})

    if porta_5m >= 6:
        score += 10
        reasons.append({"code": "VELOCITY_PORTA_ELEVATED", "weight": 10, "detail": f"porta_5m={porta_5m}"})

    # Clamp score
    score = max(0, min(100, score))

    # Decision
    if score >= thresholds["block_min"]:
        decision: Decision = "BLOCK"
    elif score >= thresholds["challenge_min"]:
        decision = "CHALLENGE"
    else:
        decision = "ALLOW"

    signals = {
        "device_hash": device_hash,
        "ip_hash": ip_hash,
        "velocity": {"ip_5m": ip_5m, "device_5m": dev_5m, "porta_5m": porta_5m},
    }

    return {
        "decision": decision,
        "score": score,
        "score_range": "0-100",
        "reasons": reasons,
        "signals": signals,
        "policy": policy,
    }
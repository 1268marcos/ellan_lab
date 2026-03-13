from typing import Any, Dict, List, Literal, Optional

from app.core.policies import get_policy_by_region


Decision = Literal["ALLOW", "CHALLENGE", "BLOCK"]


def _normalize_upper(value: Optional[str]) -> str:
    return (value or "").strip().upper()


def _append_reason(
    reasons: List[Dict[str, Any]],
    *,
    code: str,
    weight: int,
    detail: str,
) -> None:
    reasons.append(
        {
            "code": code,
            "weight": weight,
            "detail": detail,
        }
    )


def evaluate_risk(
    *,
    region: str,
    canal: str,
    metodo: str,
    valor: float,
    porta: int,
    device_known: bool,
    velocity: Dict[str, int],
    anti_replay_status: str,
    ip_hash: str,
    device_hash: str,
    card_type: Optional[str] = None,
    integration_status: str = "ACTIVE",
) -> Dict[str, Any]:
    """
    Motor de risco determinístico e auditável.

    Princípios:
      - sem random
      - score 0-100
      - reasons explicáveis
      - sensível a região, canal, método e estágio de integração

    Decisão:
      - ALLOW
      - CHALLENGE
      - BLOCK
    """
    region_u = _normalize_upper(region)
    canal_u = _normalize_upper(canal)
    metodo_u = _normalize_upper(metodo)
    anti_replay_u = _normalize_upper(anti_replay_status)
    integration_u = _normalize_upper(integration_status)
    card_type_v = (card_type or "").strip()

    policy = get_policy_by_region(region_u)
    thresholds = policy["thresholds"]

    score = 0
    reasons: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Hard blocks / integridade de requisição
    # ------------------------------------------------------------------
    if anti_replay_u == "PAYLOAD_MISMATCH":
        score += 90
        _append_reason(
            reasons,
            code="IDEMPOTENCY_PAYLOAD_MISMATCH",
            weight=90,
            detail="Idempotency-Key reutilizada com payload diferente.",
        )

    if porta < 1 or porta > 24:
        score += 80
        _append_reason(
            reasons,
            code="PORTA_OUT_OF_RANGE",
            weight=80,
            detail="Porta fora do range permitido (1-24).",
        )

    if canal_u not in {"ONLINE", "KIOSK"}:
        score += 70
        _append_reason(
            reasons,
            code="CHANNEL_INVALID",
            weight=70,
            detail=f"Canal inválido: {canal!r}.",
        )

    if region_u not in {"SP", "PT"}:
        score += 70
        _append_reason(
            reasons,
            code="REGION_INVALID",
            weight=70,
            detail=f"Região inválida: {region!r}.",
        )

    # ------------------------------------------------------------------
    # Compatibilidade método x região
    # ------------------------------------------------------------------
    if metodo_u == "PIX" and region_u != "SP":
        score += 60
        _append_reason(
            reasons,
            code="METHOD_REGION_MISMATCH_PIX",
            weight=60,
            detail="PIX não é compatível com a região informada.",
        )

    if metodo_u == "MBWAY" and region_u != "PT":
        score += 60
        _append_reason(
            reasons,
            code="METHOD_REGION_MISMATCH_MBWAY",
            weight=60,
            detail="MBWAY não é compatível com a região informada.",
        )

    if metodo_u == "MULTIBANCO_REFERENCE" and region_u != "PT":
        score += 60
        _append_reason(
            reasons,
            code="METHOD_REGION_MISMATCH_MULTIBANCO",
            weight=60,
            detail="MULTIBANCO_REFERENCE não é compatível com a região informada.",
        )

    # ------------------------------------------------------------------
    # Estágio de integração do método
    # ------------------------------------------------------------------
    if integration_u == "PLANNED":
        score += 35
        _append_reason(
            reasons,
            code="METHOD_INTEGRATION_PLANNED",
            weight=35,
            detail="Método ainda está marcado como planejado/aguardando integração.",
        )
    elif integration_u == "DISABLED":
        score += 85
        _append_reason(
            reasons,
            code="METHOD_INTEGRATION_DISABLED",
            weight=85,
            detail="Método marcado como desabilitado.",
        )

    # ------------------------------------------------------------------
    # Sinal de dispositivo
    # ------------------------------------------------------------------
    if not device_known:
        score += 15
        _append_reason(
            reasons,
            code="DEVICE_NEW",
            weight=15,
            detail="Primeira vez deste dispositivo.",
        )
    else:
        score -= 5
        _append_reason(
            reasons,
            code="DEVICE_KNOWN",
            weight=-5,
            detail="Dispositivo já visto anteriormente.",
        )

    # ------------------------------------------------------------------
    # Canal
    # ------------------------------------------------------------------
    if canal_u == "ONLINE":
        score += 6
        _append_reason(
            reasons,
            code="CHANNEL_ONLINE",
            weight=6,
            detail="Canal online possui superfície de risco maior que kiosk presencial.",
        )
    elif canal_u == "KIOSK":
        score -= 3
        _append_reason(
            reasons,
            code="CHANNEL_KIOSK",
            weight=-3,
            detail="Canal kiosk reduz parte do risco remoto, mas não elimina fraude.",
        )

    # ------------------------------------------------------------------
    # Método de pagamento
    # ------------------------------------------------------------------
    if metodo_u in {"CARTAO", "CARD"}:
        score += 14
        _append_reason(
            reasons,
            code="PAYMENT_METHOD_CARD",
            weight=14,
            detail="Cartão com digitação manual exige cautela adicional.",
        )

        if card_type_v == "creditCard":
            score += 4
            _append_reason(
                reasons,
                code="CARD_TYPE_CREDIT",
                weight=4,
                detail="Cartão de crédito possui risco ligeiramente maior nesta fase manual.",
            )
        elif card_type_v == "debitCard":
            score += 2
            _append_reason(
                reasons,
                code="CARD_TYPE_DEBIT",
                weight=2,
                detail="Cartão de débito mantém risco, porém abaixo do crédito.",
            )
        else:
            score += 8
            _append_reason(
                reasons,
                code="CARD_TYPE_MISSING",
                weight=8,
                detail="Tipo do cartão ausente ou inválido.",
            )

    elif metodo_u == "PIX":
        score += 5
        _append_reason(
            reasons,
            code="PAYMENT_METHOD_PIX",
            weight=5,
            detail="PIX requer monitorização de confirmação assíncrona.",
        )

    elif metodo_u == "MBWAY":
        score += 6
        _append_reason(
            reasons,
            code="PAYMENT_METHOD_MBWAY",
            weight=6,
            detail="MBWAY depende de aprovação externa no dispositivo do cliente.",
        )

    elif metodo_u == "MULTIBANCO_REFERENCE":
        score += 2
        _append_reason(
            reasons,
            code="PAYMENT_METHOD_MULTIBANCO",
            weight=2,
            detail="Referência Multibanco é método instrucional e assíncrono.",
        )

    elif metodo_u == "NFC":
        score += 10
        _append_reason(
            reasons,
            code="PAYMENT_METHOD_NFC",
            weight=10,
            detail="NFC exige cautela por dependência de hardware e integração presencial.",
        )

    elif metodo_u in {"APPLE_PAY", "GOOGLE_PAY", "MERCADO_PAGO_WALLET"}:
        score += 8
        _append_reason(
            reasons,
            code="PAYMENT_METHOD_DIGITAL_WALLET",
            weight=8,
            detail="Carteira digital requer validação da trilha de integração e capability do dispositivo.",
        )

    else:
        score += 20
        _append_reason(
            reasons,
            code="PAYMENT_METHOD_UNKNOWN",
            weight=20,
            detail=f"Método não reconhecido pelo motor: {metodo!r}.",
        )

    # ------------------------------------------------------------------
    # Valor
    # ------------------------------------------------------------------
    if valor >= 500:
        score += 20
        _append_reason(
            reasons,
            code="HIGH_VALUE",
            weight=20,
            detail="Valor alto para o contexto atual.",
        )
    elif valor >= 200:
        score += 8
        _append_reason(
            reasons,
            code="MID_VALUE",
            weight=8,
            detail="Valor acima do padrão esperado.",
        )
    elif valor <= 0:
        score += 70
        _append_reason(
            reasons,
            code="INVALID_VALUE",
            weight=70,
            detail="Valor inválido para pagamento.",
        )

    # ------------------------------------------------------------------
    # Velocity
    # ------------------------------------------------------------------
    ip_5m = int(velocity.get("ip_5m", 0))
    dev_5m = int(velocity.get("device_5m", 0))
    porta_5m = int(velocity.get("porta_5m", 0))

    if ip_5m >= 15:
        score += 25
        _append_reason(
            reasons,
            code="VELOCITY_IP_SPIKE",
            weight=25,
            detail=f"Explosão de tráfego por IP em 5m: ip_5m={ip_5m}.",
        )
    elif ip_5m >= 8:
        score += 12
        _append_reason(
            reasons,
            code="VELOCITY_IP_ELEVATED",
            weight=12,
            detail=f"Elevação de tráfego por IP em 5m: ip_5m={ip_5m}.",
        )

    if dev_5m >= 10:
        score += 18
        _append_reason(
            reasons,
            code="VELOCITY_DEVICE_SPIKE",
            weight=18,
            detail=f"Explosão de tentativas por dispositivo em 5m: device_5m={dev_5m}.",
        )
    elif dev_5m >= 6:
        score += 10
        _append_reason(
            reasons,
            code="VELOCITY_DEVICE_ELEVATED",
            weight=10,
            detail=f"Elevação de tentativas por dispositivo em 5m: device_5m={dev_5m}.",
        )

    if porta_5m >= 6:
        score += 10
        _append_reason(
            reasons,
            code="VELOCITY_PORTA_ELEVATED",
            weight=10,
            detail=f"Múltiplas tentativas concentradas na mesma porta em 5m: porta_5m={porta_5m}.",
        )

    # ------------------------------------------------------------------
    # Regras compostas
    # ------------------------------------------------------------------
    if metodo_u in {"CARTAO", "CARD"} and not device_known and canal_u == "ONLINE":
        score += 8
        _append_reason(
            reasons,
            code="COMBINED_CARD_NEW_DEVICE_ONLINE",
            weight=8,
            detail="Cartão + dispositivo novo + canal online aumenta risco composto.",
        )

    if metodo_u == "PIX" and ip_5m >= 15:
        score += 5
        _append_reason(
            reasons,
            code="COMBINED_PIX_IP_SPIKE",
            weight=5,
            detail="PIX sob pico de IP merece cautela adicional.",
        )

    if metodo_u == "MBWAY" and dev_5m >= 10:
        score += 5
        _append_reason(
            reasons,
            code="COMBINED_MBWAY_DEVICE_SPIKE",
            weight=5,
            detail="MBWAY com spike por dispositivo sugere comportamento anómalo.",
        )

    if metodo_u == "NFC" and integration_u != "ACTIVE":
        score += 20
        _append_reason(
            reasons,
            code="COMBINED_NFC_NOT_ACTIVE",
            weight=20,
            detail="NFC solicitado sem trilha de integração plenamente ativa.",
        )

    # ------------------------------------------------------------------
    # Clamp
    # ------------------------------------------------------------------
    score = max(0, min(100, score))

    # ------------------------------------------------------------------
    # Decisão
    # ------------------------------------------------------------------
    if score >= thresholds["block_min"]:
        decision: Decision = "BLOCK"
    elif score >= thresholds["challenge_min"]:
        decision = "CHALLENGE"
    else:
        decision = "ALLOW"

    signals = {
        "region": region_u,
        "channel": canal_u,
        "payment_method": metodo_u,
        "card_type": card_type_v or None,
        "integration_status": integration_u,
        "device_hash": device_hash,
        "ip_hash": ip_hash,
        "velocity": {
            "ip_5m": ip_5m,
            "device_5m": dev_5m,
            "porta_5m": porta_5m,
        },
    }

    return {
        "decision": decision,
        "score": score,
        "score_range": "0-100",
        "reasons": reasons,
        "signals": signals,
        "policy": policy,
    }
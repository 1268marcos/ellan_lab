from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.data.world_locker_payment_players import PAYMENT_ECOSYSTEM_SEGMENTS
from app.models.cross_domain import PaymentEcosystemPlayer, PaymentPlayerIntegration
from app.schemas.ecosystem_pro import (
    IntegrationPlaybookOut,
    PlayerIntegrationListOut,
    PlayerIntegrationOut,
)

router = APIRouter(prefix="/player-integrations", tags=["player-integrations"])

_PLAYBOOK: dict[str, dict] = {
    "LOCKER_NETWORK": {
        "domains": ["runtime", "payment_gateway", "order_pickup", "fiscal"],
        "steps": [
            "Cadastrar rede em payment_ecosystem_player (segment LOCKER_NETWORK).",
            "Mapear lockers em runtime + locker_payment_methods (payment_gateway_admin).",
            "Configurar webhook device registry e risk events.",
            "Ligar corredor fiscal/câmbio via metadata fiscal_corridor_code.",
        ],
    },
    "LOCKER_NETWORK_OPERATOR": {
        "domains": ["finance", "order_pickup", "payment_gateway"],
        "steps": [
            "Registrar operador (DPD, USPS, DHL Packstation) como LOCKER_NETWORK_OPERATOR.",
            "Criar relação OPERATES_NETWORK com rede hardware (InPost, etc.).",
            "Conciliação por lote payment_reconciliation_batch.",
        ],
    },
    "CARRIER_LAST_MILE": {
        "domains": ["order_pickup", "finance", "payment_gateway"],
        "steps": [
            "Integrar label API + tracking webhook.",
            "payment_order_context.carrier_partner_id + CHANNEL_USES_CARRIER.",
            "Splits para repasse carrier em payment_splits.",
        ],
    },
    "MARKETPLACE": {
        "domains": ["marketplace", "finance", "fiscal", "payment_gateway"],
        "steps": [
            "Webhook marketplace → webhook_endpoints.",
            "Split settlement (payment_splits) + partner_payment_holds.",
            "Catálogo seller em marketplace_admin.",
        ],
    },
    "COLLECTION_POINT": {
        "domains": ["marketplace", "order_pickup", "fiscal"],
        "steps": [
            "WHITE_LABEL relação marketplace → ponto coleta.",
            "Instrução PIX/boleto em payment_instructions.",
            "NF no locker: fiscal_admin + order_pickup.",
        ],
    },
    "LOGISTICS_PLATFORM": {
        "domains": ["finance", "payment_gateway", "order_pickup"],
        "steps": [
            "API agregadora: múltiplos carriers via AGGREGATES relations.",
            "Idempotência gateway + Melhor Envio/EasyPost pattern.",
        ],
    },
    "FOOD_DELIVERY": {
        "domains": ["order_pickup", "runtime"],
        "steps": [
            "Webhook pedido pronto + handoff locker slot.",
            "Pagamento totem ou pré-pago app — integração roadmap.",
        ],
    },
    "PAYMENTS_FISCAL": {
        "domains": ["payment_gateway", "finance", "fiscal"],
        "steps": [
            "PSP credentials em payment_provider_partners.",
            "SETTLEMENT_VIA relation para marketplace.",
        ],
    },
}


@router.get("/playbook/{segment_code}", response_model=IntegrationPlaybookOut)
def integration_playbook(segment_code: str, db: Session = Depends(get_db)) -> IntegrationPlaybookOut:
    code = segment_code.upper()
    seg = next((s for s in PAYMENT_ECOSYSTEM_SEGMENTS if s["code"] == code), None)
    if not seg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="segment_not_found")
    pb = _PLAYBOOK.get(code, {"domains": ["order_pickup"], "steps": ["Definir integração custom."]})
    examples = (
        db.query(PaymentEcosystemPlayer.code)
        .filter(PaymentEcosystemPlayer.segment == code, PaymentEcosystemPlayer.is_active.is_(True))
        .limit(8)
        .all()
    )
    return IntegrationPlaybookOut(
        segment_code=code,
        segment_name=seg["name"],
        recommended_protocol="REST",
        linked_domains=pb["domains"],
        steps=pb["steps"],
        example_players=[e[0] for e in examples],
    )


@router.get("", response_model=PlayerIntegrationListOut)
def list_integrations(
    min_readiness: int | None = Query(None, ge=0, le=100),
    production_only: bool = Query(False),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> PlayerIntegrationListOut:
    q = db.query(PaymentPlayerIntegration)
    if min_readiness is not None:
        q = q.filter(PaymentPlayerIntegration.readiness_score >= min_readiness)
    if production_only:
        q = q.filter(PaymentPlayerIntegration.production_ready.is_(True))
    items = q.order_by(PaymentPlayerIntegration.readiness_score.desc()).limit(limit).all()
    out = [PlayerIntegrationOut.model_validate(i) for i in items]
    return PlayerIntegrationListOut(items=out, total=len(out))


@router.get("/{player_code}", response_model=PlayerIntegrationOut)
def get_integration(player_code: str, db: Session = Depends(get_db)) -> PlayerIntegrationOut:
    row = (
        db.query(PaymentPlayerIntegration)
        .filter(PaymentPlayerIntegration.player_code == player_code.upper())
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="integration_not_found")
    return PlayerIntegrationOut.model_validate(row)

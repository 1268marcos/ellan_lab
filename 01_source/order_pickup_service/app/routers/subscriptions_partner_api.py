"""API B2B de parceiros para consulta de assinaturas e elegibilidade de benefícios."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.subscriptions_partner_auth import SubscriptionPartnerAuth, require_subscription_partner
from app.schemas.subscriptions_api import (
    PartnerBenefitCheckIn,
    PartnerSubscriberOut,
    PartnerWebhookAckOut,
    PartnerWebhookEventIn,
    PublicBenefitCheckOut,
)
from app.services import subscriptions_api_service as svc

router = APIRouter(
    prefix="/api/subscriptions/partner/v1",
    tags=["subscriptions-partner"],
)


@router.get("/health")
def partner_health(auth: SubscriptionPartnerAuth = Depends(require_subscription_partner())):
    return {"ok": True, "partner_code": auth.partner_code, "scopes": sorted(auth.scopes)}


@router.get("/subscribers/{user_id}", response_model=PartnerSubscriberOut)
def partner_lookup_subscriber(
    user_id: str,
    auth: SubscriptionPartnerAuth = Depends(require_subscription_partner(required_scope="subscriptions:read")),
    db: Session = Depends(get_db),
):
    sub_row = svc.fetch_active_subscription(db, user_id.strip())
    if not sub_row:
        return PartnerSubscriberOut(found=False, user_id=user_id, subscription=None, plan=None, benefits=None)

    sub = svc.subscription_to_public(sub_row)
    plan = svc.fetch_plan_summary(db, sub.plan_type)
    return PartnerSubscriberOut(
        found=True,
        user_id=user_id,
        subscription=sub,
        plan=plan,
        benefits=sub.benefits,
    )


@router.post("/benefit-check", response_model=PublicBenefitCheckOut)
def partner_benefit_check(
    body: PartnerBenefitCheckIn,
    auth: SubscriptionPartnerAuth = Depends(require_subscription_partner(required_scope="subscriptions:read")),
    db: Session = Depends(get_db),
):
    """Valida se o usuário pode usar um benefício no checkout do parceiro."""
    _ = auth
    result = svc.check_benefit_eligibility(
        db,
        body.user_id.strip(),
        body.benefit_type,
        allow_past_due=True,
    )
    return PublicBenefitCheckOut(
        eligible=bool(result.get("eligible")),
        benefit_type=body.benefit_type,
        reason=result.get("reason"),
        subscription_id=result.get("subscription_id"),
        plan_type=result.get("plan_type"),
        usage_count=result.get("usage_count"),
        usage_limit=result.get("usage_limit"),
    )


@router.post("/events", response_model=PartnerWebhookAckOut)
def partner_ingest_event(
    body: PartnerWebhookEventIn,
    auth: SubscriptionPartnerAuth = Depends(require_subscription_partner(required_scope="subscriptions:webhook")),
    db: Session = Depends(get_db),
):
    """
    Canal opcional para o parceiro notificar eventos (ex.: conversão de referral).
    Não substitui webhooks outbound configurados em OPS; serve para telemetria B2B.
    """
    if not body.subscription_id and not body.user_id:
        raise HTTPException(
            status_code=422,
            detail={"type": "MISSING_SUBJECT", "message": "Informe subscription_id ou user_id."},
        )
    return PartnerWebhookAckOut(
        accepted=True,
        event_type=body.event_type,
        note=f"received from partner={auth.partner_code}",
    )

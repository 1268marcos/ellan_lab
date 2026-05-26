"""API pública B2C de assinaturas (usuário autenticado com e-mail verificado)."""
from __future__ import annotations

import secrets
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_verified_public_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.subscriptions_api import (
    PublicBenefitCheckIn,
    PublicBenefitCheckOut,
    PublicCancelIn,
    PublicEntitlementsOut,
    PublicInvoicesOut,
    PublicMySubscriptionOut,
    PublicPlansCatalogOut,
    PublicReferralOut,
    PublicPromoRedemptionOut,
    PublicSubscribeIn,
)
from app.services import subscriptions_api_service as svc

router = APIRouter(prefix="/public/subscriptions", tags=["public-subscriptions"])


def _build_my_response(db: Session, user_id: str) -> PublicMySubscriptionOut:
    sub_row = svc.fetch_active_subscription(db, user_id)
    if not sub_row:
        return PublicMySubscriptionOut(has_subscription=False)

    sub = svc.subscription_to_public(sub_row)
    plan = svc.fetch_plan_summary(db, sub.plan_type)
    sid = str(sub_row["id"])
    return PublicMySubscriptionOut(
        has_subscription=True,
        subscription=sub,
        plan=plan,
        usage=svc.fetch_usage_for_subscription(db, sid),
        benefits_usage=svc.fetch_benefits_usage(db, sid),
        loyalty=svc.fetch_loyalty_balance(db, user_id),
        entitled_players_count=svc.count_entitlements(db, sub.plan_type),
    )


@router.get("/my", response_model=PublicMySubscriptionOut)
def my_subscription(
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    """Visão consolidada da assinatura ativa, plano, uso de benefícios e loyalty."""
    return _build_my_response(db, str(user.id))


@router.get("/my/plans", response_model=PublicPlansCatalogOut)
def my_available_plans(
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    """Catálogo de planos disponíveis para contratação ou upgrade."""
    items = svc.list_public_plans(db)
    return PublicPlansCatalogOut(items=items, total=len(items))


@router.get("/my/usage", response_model=PublicMySubscriptionOut)
def my_usage(
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    """Atalho focado em uso mensal e contadores de benefícios (mesmo payload que /my)."""
    return _build_my_response(db, str(user.id))


@router.get("/my/invoices", response_model=PublicInvoicesOut)
def my_invoices(
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    sub_row = svc.fetch_active_subscription(db, str(user.id))
    if not sub_row:
        return PublicInvoicesOut(items=[], total=0)
    items = svc.list_invoices_for_subscription(db, str(sub_row["id"]))
    return PublicInvoicesOut(items=items, total=len(items))


@router.get("/my/entitlements", response_model=PublicEntitlementsOut)
def my_entitlements(
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    sub_row = svc.fetch_active_subscription(db, str(user.id))
    if not sub_row:
        raise HTTPException(
            status_code=404,
            detail={"type": "NO_SUBSCRIPTION", "message": "Nenhuma assinatura ativa."},
        )
    plan_code = str(sub_row["plan_type"])
    items = svc.list_entitlements_for_plan(db, plan_code)
    return PublicEntitlementsOut(plan_code=plan_code, items=items, total=len(items))


@router.get("/my/loyalty")
def my_loyalty(
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    loyalty = svc.fetch_loyalty_balance(db, str(user.id))
    history = db.execute(
        text(
            """
            SELECT points_delta, reason, balance_after, created_at
            FROM subscription_loyalty_ledger
            WHERE user_id = :u ORDER BY created_at DESC LIMIT 30
            """
        ),
        {"u": str(user.id)},
    ).mappings().all()
    return {
        "ok": True,
        "balance": loyalty.balance,
        "history": [dict(h) for h in history],
    }


@router.post("/my/benefit-check", response_model=PublicBenefitCheckOut)
def my_benefit_check(
    body: PublicBenefitCheckIn,
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    result = svc.check_benefit_eligibility(db, str(user.id), body.benefit_type)
    return PublicBenefitCheckOut(
        eligible=bool(result.get("eligible")),
        benefit_type=body.benefit_type,
        reason=result.get("reason"),
        subscription_id=result.get("subscription_id"),
        plan_type=result.get("plan_type"),
        usage_count=result.get("usage_count"),
        usage_limit=result.get("usage_limit"),
    )


@router.post("/my/subscribe", response_model=PublicMySubscriptionOut)
def my_subscribe(
    body: PublicSubscribeIn,
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    promo_applied: PublicPromoRedemptionOut | None = None
    try:
        _, promo_applied = svc.create_subscription_for_user(
            db,
            user_id=str(user.id),
            plan_code=body.plan_code,
            billing_cycle=body.billing_cycle,
            partner_code=body.partner_code,
            trial_days=body.trial_days,
            promo_code=body.promo_code,
        )
    except ValueError as exc:
        code = str(exc)
        if code == "ALREADY_SUBSCRIBED":
            raise HTTPException(
                status_code=409,
                detail={"type": "ALREADY_SUBSCRIBED", "message": "Já existe assinatura ativa."},
            ) from exc
        if code.startswith("PLAN_NOT_FOUND"):
            raise HTTPException(
                status_code=422,
                detail={"type": "PLAN_NOT_FOUND", "message": body.plan_code},
            ) from exc
        if code.startswith("PROMO_INVALID:"):
            reason = code.split(":", 1)[1]
            raise HTTPException(
                status_code=422,
                detail={"type": "PROMO_INVALID", "message": reason},
            ) from exc
        raise
    out = _build_my_response(db, str(user.id))
    out.promo_applied = promo_applied
    return out


@router.post("/my/cancel")
def my_cancel(
    body: PublicCancelIn,
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    sid = svc.cancel_subscription_for_user(db, str(user.id), immediate=body.immediate)
    if not sid:
        raise HTTPException(
            status_code=404,
            detail={"type": "NO_SUBSCRIPTION", "message": "Nenhuma assinatura ativa para cancelar."},
        )
    return {"ok": True, "subscription_id": sid, "immediate": body.immediate}


@router.get("/my/referral", response_model=PublicReferralOut)
def my_referral(
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text(
            """
            SELECT referral_code, reward_cents, status
            FROM subscription_referrals
            WHERE referrer_user_id = :u AND status IN ('ACTIVE', 'PENDING')
            ORDER BY created_at DESC LIMIT 1
            """
        ),
        {"u": str(user.id)},
    ).mappings().first()
    if row:
        return PublicReferralOut(
            referral_code=str(row["referral_code"]),
            reward_cents=int(row["reward_cents"]),
            status=str(row["status"]),
        )
    code = f"ELLAN-{secrets.token_hex(3).upper()}"
    rid = str(uuid.uuid4())
    now = svc.utc_now()
    db.execute(
        text(
            """
            INSERT INTO subscription_referrals (
                id, referrer_user_id, referral_code, reward_cents, status, created_at
            ) VALUES (:id, :uid, :code, 500, 'ACTIVE', :now)
            """
        ),
        {"id": rid, "uid": str(user.id), "code": code, "now": now},
    )
    db.commit()
    return PublicReferralOut(referral_code=code, reward_cents=500, status="ACTIVE")


@router.get("/my/regional-price")
def my_regional_price(
    region: str = Query("BR", min_length=2, max_length=8),
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    sub_row = svc.fetch_active_subscription(db, str(user.id))
    plan_code = str(sub_row["plan_type"]) if sub_row else "PREMIUM"
    row = db.execute(
        text(
            """
            SELECT plan_code, region_code, currency, monthly_fee_cents, yearly_fee_cents, tax_inclusive
            FROM subscription_regional_prices
            WHERE plan_code = :plan AND region_code = :reg AND active = TRUE LIMIT 1
            """
        ),
        {"plan": plan_code.upper(), "reg": region.strip().upper()},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"type": "REGIONAL_PRICE_NOT_FOUND", "message": f"{plan_code}/{region}"},
        )
    return {"ok": True, "pricing": dict(row), "has_subscription": sub_row is not None}


@router.get("/my/addons")
def my_addons(
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    sub_row = svc.fetch_active_subscription(db, str(user.id))
    if not sub_row:
        catalog = db.execute(
            text("SELECT code, name, addon_type, monthly_fee_cents FROM subscription_plan_addons WHERE active = TRUE")
        ).mappings().all()
        return {"ok": True, "has_subscription": False, "active": [], "catalog": [dict(r) for r in catalog]}

    active = db.execute(
        text(
            """
            SELECT a.addon_code, a.monthly_fee_cents, a.status, p.name, p.addon_type
            FROM subscription_active_addons a
            JOIN subscription_plan_addons p ON p.code = a.addon_code
            WHERE a.subscription_id = :sid AND a.status = 'ACTIVE'
            """
        ),
        {"sid": str(sub_row["id"])},
    ).mappings().all()
    return {"ok": True, "has_subscription": True, "active": [dict(r) for r in active], "catalog": []}


@router.get("/my/retention-offer")
def my_retention_offer(
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    sub_row = svc.fetch_active_subscription(db, str(user.id))
    if not sub_row:
        return {"ok": True, "offer": None}
    row = db.execute(
        text(
            """
            SELECT id, offer_code, discount_pct, bonus_months, valid_until, status
            FROM subscription_retention_offers
            WHERE subscription_id = :sid AND status = 'OFFERED' AND valid_until >= :now
            ORDER BY created_at DESC LIMIT 1
            """
        ),
        {"sid": str(sub_row["id"]), "now": svc.utc_now()},
    ).mappings().first()
    return {"ok": True, "offer": dict(row) if row else None}


@router.post("/my/retention-offer/{offer_id}/accept")
def my_accept_retention(
    offer_id: str,
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    sub_row = svc.fetch_active_subscription(db, str(user.id))
    if not sub_row:
        raise HTTPException(status_code=404, detail={"type": "NO_SUBSCRIPTION", "message": "Sem assinatura"})
    now = svc.utc_now()
    row = db.execute(
        text(
            """
            SELECT id, discount_pct, bonus_months FROM subscription_retention_offers
            WHERE id = :id AND subscription_id = :sid AND status = 'OFFERED' AND valid_until >= :now
            LIMIT 1
            """
        ),
        {"id": offer_id, "sid": str(sub_row["id"]), "now": now},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "OFFER_NOT_FOUND", "message": offer_id})
    period_end = now + timedelta(days=30 * (1 + int(row["bonus_months"] or 0)))
    db.execute(
        text(
            "UPDATE subscription_retention_offers SET status = 'ACCEPTED', accepted_at = :now WHERE id = :id"
        ),
        {"id": offer_id, "now": now},
    )
    db.execute(
        text(
            """
            UPDATE customer_subscriptions
            SET cancel_at_period_end = FALSE, current_period_end = :end, next_billing_at = :end, updated_at = :now
            WHERE id = :sid
            """
        ),
        {"sid": str(sub_row["id"]), "end": period_end, "now": now},
    )
    db.commit()
    return {"ok": True, "discount_pct": float(row["discount_pct"]), "current_period_end": period_end.isoformat()}


@router.post("/promo/validate")
def public_validate_promo(
    code: str = Query(..., min_length=1),
    plan_code: str = Query(..., min_length=1),
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    from app.services import subscription_promo_service as promo_svc

    return promo_svc.validate_promo(
        db, code=code, user_id=str(user.id), plan_code=plan_code
    )


@router.get("/my/upgrade-suggestions")
def my_upgrade_suggestions(
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    from app.routers.subscriptions_efficiency import upgrade_matrix

    data = upgrade_matrix(db)
    uid = str(user.id)
    items = [i for i in data.get("items", []) if str(i.get("user_id")) == uid]
    return {"ok": True, "period_month": data.get("period_month"), "items": items, "total": len(items)}


@router.post("/my/change-plan")
def my_change_plan(
    body: PublicSubscribeIn,
    user: User = Depends(get_current_verified_public_user),
    db: Session = Depends(get_db),
):
    from app.routers.subscriptions_efficiency import PlanChangeIn, change_subscription_plan

    sub_row = svc.fetch_active_subscription(db, str(user.id))
    if not sub_row:
        raise HTTPException(status_code=404, detail={"type": "NO_SUBSCRIPTION", "message": "Sem assinatura"})
    return change_subscription_plan(
        PlanChangeIn(
            subscription_id=str(sub_row["id"]),
            to_plan_code=body.plan_code,
            actor_id=str(user.id),
            notes="public_api",
        ),
        db,
    )

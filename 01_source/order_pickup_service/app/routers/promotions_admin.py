from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_user, require_user_roles
from app.core.db import get_db
from app.core.promotions_players_integration import (
    catalog_segments_summary,
    load_players_catalog,
    seed_player_aliases_and_relations,
    validate_player_scope,
)
from app.core.global_players_seed import seed_global_players_registry
from app.core.promotions_seed import seed_promotions_world
from app.services.promotion_engine_service import (
    detect_scope_conflicts,
    match_promotions,
    player_promotion_matrix,
    record_promotion_audit,
    simulate_promotion,
)
from app.models.user import User
from app.routers.pricing_fiscal import _conditions_json_sql_value, _json_load_dict, _to_iso_utc


def _metadata_json_sql(db: Session) -> str:
    return _conditions_json_sql_value(db).replace("conditions_json", "metadata_json")
from app.schemas.promotions_admin import (
    PromotionCampaignCreateIn,
    PromotionCampaignListOut,
    PromotionCampaignOut,
    PromotionCampaignStatusPatchIn,
    LockerPlayerCatalogOut,
    PlayerMatrixSummary,
    PlayerSegmentSummary,
    PromotionLockerPlayerOut,
    PromotionOverviewOut,
    PromotionProductInclusionCreateIn,
    PromotionProductInclusionListOut,
    PromotionProductInclusionOut,
    PromotionRedemptionListOut,
    PromotionRedemptionOut,
    PromotionScopeCreateIn,
    PromotionScopeListOut,
    PromotionScopeOut,
    PromotionAuditListOut,
    PromotionAuditEventOut,
    PromotionConflictsOut,
    PromotionConflictOut,
    PromotionMatchIn,
    PromotionMatchOut,
    PromotionMatchItemOut,
    PromotionSimulateIn,
    PromotionSimulateOut,
    PlayerPromotionMatrixOut,
    PromotionWorldSeedOut,
)

router = APIRouter(
    tags=["promotions-admin"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao", "auditoria"}))],
)


def _campaign_to_out(row: dict, promotions_count: int = 0) -> PromotionCampaignOut:
    return PromotionCampaignOut(
        id=str(row.get("id") or ""),
        code=str(row.get("code") or ""),
        name=str(row.get("name") or ""),
        description=(str(row.get("description")) if row.get("description") is not None else None),
        channel_family=str(row.get("channel_family") or "GENERAL"),
        primary_country=(str(row.get("primary_country")) if row.get("primary_country") is not None else None),
        priority=int(row.get("priority") or 100),
        max_stack_promotions=int(row.get("max_stack_promotions") or 1),
        is_active=bool(row.get("is_active")),
        valid_from=_to_iso_utc(row.get("valid_from")),
        valid_until=_to_iso_utc(row.get("valid_until")) if row.get("valid_until") else None,
        metadata_json=_json_load_dict(row.get("metadata_json"), default={}),
        promotions_count=int(promotions_count),
        created_at=_to_iso_utc(row.get("created_at")),
    )


@router.get("/promotions/overview", response_model=PromotionOverviewOut)
def promotions_overview(db: Session = Depends(get_db)):
    prom_total = int(db.execute(text("SELECT COUNT(*) FROM promotions")).scalar() or 0)
    prom_active = int(
        db.execute(text("SELECT COUNT(*) FROM promotions WHERE is_active = TRUE")).scalar() or 0
    )
    camp_total = int(db.execute(text("SELECT COUNT(*) FROM promotion_campaigns")).scalar() or 0)
    camp_active = int(
        db.execute(text("SELECT COUNT(*) FROM promotion_campaigns WHERE is_active = TRUE")).scalar() or 0
    )
    red_total = int(db.execute(text("SELECT COUNT(*) FROM promotion_redemptions")).scalar() or 0)
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    red_24h = int(
        db.execute(
            text("SELECT COUNT(*) FROM promotion_redemptions WHERE redeemed_at >= :since"),
            {"since": since},
        ).scalar()
        or 0
    )
    top_codes = db.execute(
        text(
            """
            SELECT p.code, COUNT(r.id) AS cnt
            FROM promotion_redemptions r
            JOIN promotions p ON p.id = r.promotion_id
            GROUP BY p.code
            ORDER BY cnt DESC
            LIMIT 8
            """
        )
    ).mappings().all()
    top_players = db.execute(
        text(
            """
            SELECT scope_value AS player_code, COUNT(*) AS cnt
            FROM promotion_scopes
            WHERE scope_type IN ('PLAYER', 'MARKETPLACE', 'LOCKER_OPERATOR')
            GROUP BY scope_value
            ORDER BY cnt DESC
            LIMIT 10
            """
        )
    ).mappings().all()
    featured = [
        "INPOST",
        "DHL",
        "MAGALU",
        "MERCADO_LIVRE",
        "AMAZON",
        "DPD",
        "CORREIOS",
        "CTT",
        "WORTEN",
        "EL_CORTE_INGLES",
    ]
    return PromotionOverviewOut(
        promotions_total=prom_total,
        promotions_active=prom_active,
        campaigns_total=camp_total,
        campaigns_active=camp_active,
        redemptions_24h=red_24h,
        redemptions_total=red_total,
        top_promotion_codes=[{"code": r.get("code"), "redemptions": int(r.get("cnt") or 0)} for r in top_codes],
        top_player_scopes=[
            {"player_code": r.get("player_code"), "scopes": int(r.get("cnt") or 0)} for r in top_players
        ],
        locker_players_catalog_size=len(load_players_catalog(db)),
        featured_locker_players=featured,
        player_segments=[
            PlayerSegmentSummary(segment=str(s["segment"]), count=int(s["count"]))
            for s in catalog_segments_summary(db)
        ],
        player_promotion_matrix=[
            PlayerMatrixSummary(
                player_code=str(m["player_code"]),
                active_promotions=int(m["active_promotions"]),
            )
            for m in player_promotion_matrix(db)
        ],
    )


@router.get("/promotions/locker-players-catalog", response_model=LockerPlayerCatalogOut)
def locker_players_catalog(
    segment: str | None = Query(default=None, description="LOCKER_OPERATOR, CARRIER, MARKETPLACE, FOOD_DELIVERY, …"),
    db: Session = Depends(get_db),
):
    featured = [
        "INPOST",
        "DHL",
        "MAGALU",
        "MERCADO_LIVRE",
        "AMAZON",
        "DPD",
        "CORREIOS",
        "CTT",
        "WORTEN",
        "EL_CORTE_INGLES",
    ]
    raw = load_players_catalog(db, segment=segment)
    items = [
        PromotionLockerPlayerOut(
            code=row["code"],
            display_name=row["display_name"],
            segment=row["segment"],
            countries=row.get("countries") or [],
            aliases=row.get("aliases") or [],
            notes=row.get("notes"),
        )
        for row in raw
    ]
    return LockerPlayerCatalogOut(total=len(items), items=items, featured_codes=featured)


@router.post("/promotions/sync-global-players")
def sync_global_players_for_promotions(db: Session = Depends(get_db)):
    """Sincroniza PLAYERS_REGISTRY → global_players + aliases + relações."""
    gp = seed_global_players_registry(db, sync_ecosystem=True)
    links = seed_player_aliases_and_relations(db)
    return {
        "ok": True,
        "global_players": gp,
        "player_aliases_inserted": links.get("aliases", 0),
        "player_relations_inserted": links.get("relations", 0),
        "catalog_total": len(load_players_catalog(db)),
        "segments": catalog_segments_summary(db),
    }


@router.post("/promotions/seed-world", response_model=PromotionWorldSeedOut)
def seed_promotions_world_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    created_by = str(current_user.id) if current_user and current_user.id else None
    counts = seed_promotions_world(db, created_by=created_by)
    return PromotionWorldSeedOut(ok=True, **counts)


@router.get("/promotion-campaigns", response_model=PromotionCampaignListOut)
def list_promotion_campaigns(
    is_active: bool | None = Query(default=None),
    channel_family: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    filters = ["1=1"]
    params: dict = {"lim": limit, "off": offset}
    if is_active is not None:
        filters.append("c.is_active = :active")
        params["active"] = bool(is_active)
    fam = str(channel_family or "").strip().upper()
    if fam:
        filters.append("c.channel_family = :fam")
        params["fam"] = fam
    where_sql = " AND ".join(filters)
    total = int(
        db.execute(text(f"SELECT COUNT(*) FROM promotion_campaigns c WHERE {where_sql}"), params).scalar() or 0
    )
    rows = db.execute(
        text(
            f"""
            SELECT c.*, (
                SELECT COUNT(*) FROM promotions p WHERE p.campaign_id = c.id
            ) AS promotions_count
            FROM promotion_campaigns c
            WHERE {where_sql}
            ORDER BY c.priority ASC, c.created_at DESC
            LIMIT :lim OFFSET :off
            """
        ),
        params,
    ).mappings().all()
    items = [
        _campaign_to_out(dict(r), promotions_count=int(r.get("promotions_count") or 0)) for r in rows
    ]
    return PromotionCampaignListOut(ok=True, total=total, limit=limit, offset=offset, items=items)


@router.post("/promotion-campaigns", response_model=PromotionCampaignOut)
def create_promotion_campaign(
    payload: PromotionCampaignCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row_id = str(uuid4())
    data = payload.model_dump(mode="json")
    meta_sql = _metadata_json_sql(db)
    now = datetime.now(timezone.utc)
    try:
        db.execute(
            text(
                f"""
                INSERT INTO promotion_campaigns (
                    id, code, name, description, channel_family, primary_country,
                    priority, max_stack_promotions, is_active, valid_from, valid_until,
                    metadata_json, created_at, updated_at
                ) VALUES (
                    :id, :code, :name, :description, :channel_family, :primary_country,
                    :priority, :max_stack_promotions, TRUE, :valid_from, :valid_until,
                    {meta_sql}, :created_at, :updated_at
                )
                """
            ),
            {
                "id": row_id,
                **data,
                "metadata_json": json.dumps(data.get("metadata_json") or {}),
                "created_at": now,
                "updated_at": now,
            },
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"type": "CAMPAIGN_CODE_CONFLICT", "message": "Código de campanha já existe."},
        ) from exc
    row = db.execute(
        text("SELECT * FROM promotion_campaigns WHERE id = :id"),
        {"id": row_id},
    ).mappings().first()
    return _campaign_to_out(dict(row or {}), promotions_count=0)


@router.patch("/promotion-campaigns/{campaign_id}/status", response_model=PromotionCampaignOut)
def patch_campaign_status(
    campaign_id: str,
    payload: PromotionCampaignStatusPatchIn,
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("SELECT id FROM promotion_campaigns WHERE id = :id"),
        {"id": campaign_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "CAMPAIGN_NOT_FOUND"})
    now = datetime.now(timezone.utc)
    db.execute(
        text(
            "UPDATE promotion_campaigns SET is_active = :a, updated_at = :u WHERE id = :id"
        ),
        {"id": campaign_id, "a": bool(payload.is_active), "u": now},
    )
    db.commit()
    full = db.execute(text("SELECT * FROM promotion_campaigns WHERE id = :id"), {"id": campaign_id}).mappings().first()
    cnt = int(
        db.execute(text("SELECT COUNT(*) FROM promotions WHERE campaign_id = :id"), {"id": campaign_id}).scalar() or 0
    )
    return _campaign_to_out(dict(full or {}), promotions_count=cnt)


@router.get("/promotions/{promotion_id}/scopes", response_model=PromotionScopeListOut)
def list_promotion_scopes(promotion_id: str, db: Session = Depends(get_db)):
    if not db.execute(text("SELECT 1 FROM promotions WHERE id = :id"), {"id": promotion_id}).scalar():
        raise HTTPException(status_code=404, detail={"type": "PROMOTION_NOT_FOUND"})
    rows = db.execute(
        text(
            """
            SELECT id, promotion_id, scope_type, scope_value, mode, notes, created_at
            FROM promotion_scopes WHERE promotion_id = :pid ORDER BY scope_type, scope_value
            """
        ),
        {"pid": promotion_id},
    ).mappings().all()
    items = [
        PromotionScopeOut(
            id=str(r.get("id") or ""),
            promotion_id=str(r.get("promotion_id") or ""),
            scope_type=str(r.get("scope_type") or ""),
            scope_value=str(r.get("scope_value") or ""),
            mode=str(r.get("mode") or "INCLUDE"),
            notes=(str(r.get("notes")) if r.get("notes") is not None else None),
            created_at=_to_iso_utc(r.get("created_at")),
        )
        for r in rows
    ]
    return PromotionScopeListOut(ok=True, promotion_id=promotion_id, total=len(items), items=items)


@router.post("/promotions/{promotion_id}/scopes", response_model=PromotionScopeOut)
def add_promotion_scope(
    promotion_id: str,
    payload: PromotionScopeCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not db.execute(text("SELECT 1 FROM promotions WHERE id = :id"), {"id": promotion_id}).scalar():
        raise HTTPException(status_code=404, detail={"type": "PROMOTION_NOT_FOUND"})
    scope_val = str(payload.scope_value).strip().upper()
    ok_player, resolved = validate_player_scope(db, str(payload.scope_type), scope_val)
    if not ok_player:
        raise HTTPException(
            status_code=400,
            detail={"type": "INVALID_PLAYER_SCOPE", "message": resolved or scope_val},
        )
    if resolved:
        scope_val = resolved
    row_id = str(uuid4())
    try:
        db.execute(
            text(
                """
                INSERT INTO promotion_scopes (id, promotion_id, scope_type, scope_value, mode, notes, created_at)
                VALUES (:id, :pid, :st, :sv, :mode, :notes, :at)
                """
            ),
            {
                "id": row_id,
                "pid": promotion_id,
                "st": str(payload.scope_type).strip().upper(),
                "sv": scope_val,
                "mode": str(payload.mode).strip().upper(),
                "notes": payload.notes,
                "at": datetime.now(timezone.utc),
            },
        )
        record_promotion_audit(
            db,
            entity_type="promotion",
            entity_id=promotion_id,
            action="SCOPE_ADDED",
            actor_id=str(current_user.id) if current_user and current_user.id else None,
            payload={"scope_type": str(payload.scope_type), "scope_value": scope_val, "mode": payload.mode},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail={"type": "SCOPE_DUPLICATE"}) from exc
    row = db.execute(text("SELECT * FROM promotion_scopes WHERE id = :id"), {"id": row_id}).mappings().first()
    return PromotionScopeOut(
        id=row_id,
        promotion_id=promotion_id,
        scope_type=str(row.get("scope_type") or ""),
        scope_value=str(row.get("scope_value") or ""),
        mode=str(row.get("mode") or ""),
        notes=payload.notes,
        created_at=_to_iso_utc(row.get("created_at")),
    )


@router.delete("/promotions/{promotion_id}/scopes/{scope_id}")
def delete_promotion_scope(promotion_id: str, scope_id: str, db: Session = Depends(get_db)):
    deleted = db.execute(
        text("DELETE FROM promotion_scopes WHERE id = :sid AND promotion_id = :pid RETURNING id"),
        {"sid": scope_id, "pid": promotion_id},
    ).scalar()
    if not deleted:
        raise HTTPException(status_code=404, detail={"type": "SCOPE_NOT_FOUND"})
    db.commit()
    return {"ok": True, "scope_id": scope_id}


@router.get("/promotions/{promotion_id}/product-inclusions", response_model=PromotionProductInclusionListOut)
def list_product_inclusions(promotion_id: str, db: Session = Depends(get_db)):
    if not db.execute(text("SELECT 1 FROM promotions WHERE id = :id"), {"id": promotion_id}).scalar():
        raise HTTPException(status_code=404, detail={"type": "PROMOTION_NOT_FOUND"})
    rows = db.execute(
        text(
            "SELECT promotion_id, product_id FROM promotion_product_inclusions WHERE promotion_id = :pid ORDER BY product_id"
        ),
        {"pid": promotion_id},
    ).mappings().all()
    items = [
        PromotionProductInclusionOut(
            promotion_id=str(r.get("promotion_id") or ""),
            product_id=str(r.get("product_id") or ""),
        )
        for r in rows
    ]
    return PromotionProductInclusionListOut(ok=True, total=len(items), items=items)


@router.post("/promotions/{promotion_id}/product-inclusions", response_model=PromotionProductInclusionOut)
def add_product_inclusion(
    promotion_id: str,
    payload: PromotionProductInclusionCreateIn,
    db: Session = Depends(get_db),
):
    if not db.execute(text("SELECT 1 FROM promotions WHERE id = :id"), {"id": promotion_id}).scalar():
        raise HTTPException(status_code=404, detail={"type": "PROMOTION_NOT_FOUND"})
    if not db.execute(text("SELECT 1 FROM products WHERE id = :id"), {"id": payload.product_id}).scalar():
        raise HTTPException(status_code=404, detail={"type": "PRODUCT_NOT_FOUND"})
    try:
        db.execute(
            text(
                "INSERT INTO promotion_product_inclusions (promotion_id, product_id) VALUES (:pid, :prid)"
            ),
            {"pid": promotion_id, "prid": payload.product_id},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail={"type": "INCLUSION_DUPLICATE"}) from exc
    return PromotionProductInclusionOut(promotion_id=promotion_id, product_id=payload.product_id)


@router.delete("/promotions/{promotion_id}/product-inclusions/{product_id}")
def delete_product_inclusion(promotion_id: str, product_id: str, db: Session = Depends(get_db)):
    deleted = db.execute(
        text(
            "DELETE FROM promotion_product_inclusions WHERE promotion_id = :pid AND product_id = :prid RETURNING product_id"
        ),
        {"pid": promotion_id, "prid": product_id},
    ).scalar()
    if not deleted:
        raise HTTPException(status_code=404, detail={"type": "INCLUSION_NOT_FOUND"})
    db.commit()
    return {"ok": True, "product_id": product_id}


@router.get("/promotion-redemptions", response_model=PromotionRedemptionListOut)
def list_promotion_redemptions(
    promotion_id: str | None = Query(default=None),
    order_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    filters = []
    params: dict = {"lim": limit, "off": offset}
    if promotion_id:
        filters.append("promotion_id = :pid")
        params["pid"] = promotion_id
    if order_id:
        filters.append("order_id = :oid")
        params["oid"] = str(order_id).strip()
    where_sql = f"WHERE {' AND '.join(filters)}" if filters else ""
    total = int(
        db.execute(text(f"SELECT COUNT(*) FROM promotion_redemptions {where_sql}"), params).scalar() or 0
    )
    rows = db.execute(
        text(
            f"""
            SELECT * FROM promotion_redemptions {where_sql}
            ORDER BY redeemed_at DESC LIMIT :lim OFFSET :off
            """
        ),
        params,
    ).mappings().all()
    items = [
        PromotionRedemptionOut(
            id=str(r.get("id") or ""),
            promotion_id=str(r.get("promotion_id") or ""),
            campaign_id=(str(r.get("campaign_id")) if r.get("campaign_id") else None),
            order_id=str(r.get("order_id") or ""),
            user_id=(str(r.get("user_id")) if r.get("user_id") else None),
            partner_id=(str(r.get("partner_id")) if r.get("partner_id") else None),
            channel_code=(str(r.get("channel_code")) if r.get("channel_code") else None),
            country_code=(str(r.get("country_code")) if r.get("country_code") else None),
            player_code=(str(r.get("player_code")) if r.get("player_code") else None),
            discount_cents=int(r.get("discount_cents") or 0),
            currency=str(r.get("currency") or "BRL"),
            redeemed_at=_to_iso_utc(r.get("redeemed_at")),
        )
        for r in rows
    ]
    return PromotionRedemptionListOut(ok=True, total=total, limit=limit, offset=offset, items=items)


@router.post("/promotions/simulate", response_model=PromotionSimulateOut)
def promotions_simulate(payload: PromotionSimulateIn, db: Session = Depends(get_db)):
    """Dry-run: calcula desconto sem gravar resgate."""
    result = simulate_promotion(
        db,
        promotion_code=payload.promotion_code,
        order_id=payload.order_id,
        total_amount_cents=payload.total_amount_cents,
        items=payload.items,
        country_code=payload.country_code,
        channel_code=payload.channel_code,
        player_code=payload.player_code,
        partner_id=payload.partner_id,
        marketplace_code=payload.marketplace_code,
    )
    return PromotionSimulateOut(ok=True, **result)


@router.post("/promotions/match", response_model=PromotionMatchOut)
def promotions_match(payload: PromotionMatchIn, db: Session = Depends(get_db)):
    """Lista promoções elegíveis para o contexto (ranking por desconto estimado)."""
    raw = match_promotions(
        db,
        total_amount_cents=payload.total_amount_cents,
        items=payload.items,
        country_code=payload.country_code,
        channel_code=payload.channel_code,
        player_code=payload.player_code,
        partner_id=payload.partner_id,
        marketplace_code=payload.marketplace_code,
        limit=payload.limit,
    )
    items = [PromotionMatchItemOut(**row) for row in raw]
    return PromotionMatchOut(ok=True, total=len(items), items=items)


@router.get("/promotions/conflicts", response_model=PromotionConflictsOut)
def promotions_conflicts(
    limit: int = Query(default=30, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Detecta sobreposição de escopos INCLUDE entre promoções ativas."""
    raw = detect_scope_conflicts(db, limit=limit)
    items = [PromotionConflictOut(**row) for row in raw]
    return PromotionConflictsOut(ok=True, total=len(items), items=items)


@router.get("/promotions/player-matrix", response_model=PlayerPromotionMatrixOut)
def promotions_player_matrix(db: Session = Depends(get_db)):
    """Heatmap: players com mais promoções ativas (escopo)."""
    return PlayerPromotionMatrixOut(ok=True, items=player_promotion_matrix(db))


@router.get("/promotion-audit-events", response_model=PromotionAuditListOut)
def list_promotion_audit_events(
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    filters = []
    params: dict = {"lim": limit}
    if entity_type:
        filters.append("entity_type = :et")
        params["et"] = entity_type.strip().upper()
    if entity_id:
        filters.append("entity_id = :eid")
        params["eid"] = entity_id.strip()
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    try:
        total = int(db.execute(text(f"SELECT COUNT(*) FROM promotion_audit_events {where}"), params).scalar() or 0)
        rows = db.execute(
            text(
                f"""
                SELECT id, entity_type, entity_id, action, actor_id, payload_json, created_at
                FROM promotion_audit_events {where}
                ORDER BY created_at DESC LIMIT :lim
                """
            ),
            params,
        ).mappings().all()
    except Exception:
        return PromotionAuditListOut(ok=True, total=0, items=[])
    items = [
        PromotionAuditEventOut(
            id=str(r.get("id") or ""),
            entity_type=str(r.get("entity_type") or ""),
            entity_id=str(r.get("entity_id") or ""),
            action=str(r.get("action") or ""),
            actor_id=(str(r.get("actor_id")) if r.get("actor_id") else None),
            created_at=_to_iso_utc(r.get("created_at")),
            payload_json=_json_load_dict(r.get("payload_json")),
        )
        for r in rows
    ]
    return PromotionAuditListOut(ok=True, total=total, items=items)

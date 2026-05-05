from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.partner_auth import require_partner_id
from app.schemas.analytics import PickupMetricsResponse
from app.schemas.analytics_breakdown import PickupBreakdownResponse
from app.schemas.analytics_executive_summary import PickupExecutiveSummaryResponse
from app.schemas.analytics_ranking import PickupRankingResponse
from app.services.pickup_breakdown_service import build_pickup_breakdown
from app.services.pickup_executive_summary_service import build_pickup_executive_summary
from app.services.pickup_metrics_service import build_pickup_metrics
from app.services.pickup_ranking_service import build_pickup_ranking

router = APIRouter(prefix="/partner", tags=["partner"])


def _safe_bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/analytics/pickup-metrics", response_model=PickupMetricsResponse)
def partner_get_pickup_metrics(
    partner_id: Annotated[str, Depends(require_partner_id)],
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    region: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    slot: str | None = Query(default=None),
    locker_id: str | None = Query(default=None),
    machine_id: str | None = Query(default=None),
    operator_id: str | None = Query(default=None),
    tenant_id: str | None = Query(default=None),
    site_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return build_pickup_metrics(
        db,
        start_at=start_at,
        end_at=end_at,
        region=region,
        channel=channel,
        slot=slot,
        locker_id=locker_id,
        machine_id=machine_id,
        operator_id=operator_id,
        tenant_id=tenant_id,
        site_id=site_id,
        ecommerce_partner_id=partner_id,
    )


@router.get("/analytics/pickup-breakdown", response_model=PickupBreakdownResponse)
def partner_get_pickup_breakdown(
    partner_id: Annotated[str, Depends(require_partner_id)],
    dimension: str = Query(...),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    region: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    slot: str | None = Query(default=None),
    locker_id: str | None = Query(default=None),
    machine_id: str | None = Query(default=None),
    operator_id: str | None = Query(default=None),
    tenant_id: str | None = Query(default=None),
    site_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        return build_pickup_breakdown(
            db,
            dimension=dimension,
            start_at=start_at,
            end_at=end_at,
            region=region,
            channel=channel,
            slot=slot,
            locker_id=locker_id,
            machine_id=machine_id,
            operator_id=operator_id,
            tenant_id=tenant_id,
            site_id=site_id,
            ecommerce_partner_id=partner_id,
        )
    except ValueError as exc:
        raise _safe_bad_request("Invalid breakdown query parameters.") from exc


@router.get("/analytics/pickup-ranking", response_model=PickupRankingResponse)
def partner_get_pickup_ranking(
    partner_id: Annotated[str, Depends(require_partner_id)],
    category: str = Query(...),
    metric: str = Query(...),
    dimension: str = Query(...),
    limit: int = Query(default=10, ge=1, le=100),
    direction: str | None = Query(default=None),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    region: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    slot: str | None = Query(default=None),
    locker_id: str | None = Query(default=None),
    machine_id: str | None = Query(default=None),
    operator_id: str | None = Query(default=None),
    tenant_id: str | None = Query(default=None),
    site_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        return build_pickup_ranking(
            db,
            category=category,
            metric=metric,
            dimension=dimension,
            limit=limit,
            direction=direction,
            start_at=start_at,
            end_at=end_at,
            region=region,
            channel=channel,
            slot=slot,
            locker_id=locker_id,
            machine_id=machine_id,
            operator_id=operator_id,
            tenant_id=tenant_id,
            site_id=site_id,
            ecommerce_partner_id=partner_id,
        )
    except ValueError as exc:
        raise _safe_bad_request("Invalid ranking query parameters.") from exc


@router.get(
    "/analytics/pickup-executive-summary",
    response_model=PickupExecutiveSummaryResponse,
)
def partner_get_pickup_executive_summary(
    partner_id: Annotated[str, Depends(require_partner_id)],
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    region: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    slot: str | None = Query(default=None),
    locker_id: str | None = Query(default=None),
    machine_id: str | None = Query(default=None),
    operator_id: str | None = Query(default=None),
    tenant_id: str | None = Query(default=None),
    site_id: str | None = Query(default=None),
    ranking_limit: int = Query(default=5, ge=1, le=20),
    trend_days_window: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    return build_pickup_executive_summary(
        db,
        start_at=start_at,
        end_at=end_at,
        region=region,
        channel=channel,
        slot=slot,
        locker_id=locker_id,
        machine_id=machine_id,
        operator_id=operator_id,
        tenant_id=tenant_id,
        site_id=site_id,
        ranking_limit=ranking_limit,
        trend_days_window=trend_days_window,
        ecommerce_partner_id=partner_id,
    )

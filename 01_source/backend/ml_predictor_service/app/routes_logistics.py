"""Rotas REST de logística (roteirização ML + OR-Tools)."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ml_routing.route_optimizer import optimize_route

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/logistics", tags=["logistics"])


class OptimizeRouteRequest(BaseModel):
    locker_ids: list[str] = Field(..., min_length=2, description="IDs dos lockers a visitar (ordem ingênua = input)")
    vehicle_capacity_parcels: int = Field(80, ge=1, le=500)
    service_time_minutes_default: float = Field(6.0, ge=0.5, le=120.0)
    time_window_start_minutes: int = Field(8 * 60, ge=0, le=24 * 60)
    time_window_end_minutes: int = Field(20 * 60, ge=0, le=24 * 60)
    k_clusters: int | None = Field(None, ge=2, le=24)


@router.post("/optimize-route")
def post_optimize_route(body: OptimizeRouteRequest) -> dict:
    if body.time_window_end_minutes <= body.time_window_start_minutes:
        raise HTTPException(400, "time_window_end_minutes deve ser maior que time_window_start_minutes")
    try:
        return optimize_route(
            [str(x).strip() for x in body.locker_ids if str(x).strip()],
            vehicle_capacity_parcels=body.vehicle_capacity_parcels,
            service_time_minutes_default=float(body.service_time_minutes_default),
            time_window_start_minutes=body.time_window_start_minutes,
            time_window_end_minutes=body.time_window_end_minutes,
            k_clusters=body.k_clusters,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception:
        logger.exception("optimize-route failed")
        raise HTTPException(500, "falha ao otimizar rota") from None

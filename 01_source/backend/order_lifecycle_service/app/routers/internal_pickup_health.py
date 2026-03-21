# 01_source/backend/order_lifecycle/app/routers/internal_pickup_health.py
# LEGADO
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from app.services.pickup_health_service import compute_health


router = APIRouter(
    prefix="/internal/analytics/pickup-health",
    tags=["internal-analytics-pickup-health"],
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# =========================================================
# MOCK ADAPTER (TEMPORÁRIO ATÉ CONECTAR COM ANALYTICS REAL)
# =========================================================

def _mock_entities() -> List[Dict[str, Any]]:
    """
    ⚠️ TEMPORÁRIO
    Substituir depois pelos dados reais do analytics.
    """
    return [
        {
            "entity_type": "locker",
            "entity_id": "locker-sp-001",
            "tenant_id": "tenant_br",
            "operator_id": "op_sp",
            "region": "SP",
            "site_id": "site_sp_centro",
            "machine_id": "machine_sp_01",
            "locker_id": "locker-sp-001",
            "signals": {
                "pickup_success_rate": 0.82,
                "expiration_rate": 0.08,
                "cancel_rate": 0.04,
                "avg_pickup_minutes": 38,
                "trend_direction": "stable",
                "saturation_level": "medium",
                "sample_size": 120,
            },
        },
        {
            "entity_type": "locker",
            "entity_id": "locker-sp-002",
            "tenant_id": "tenant_br",
            "operator_id": "op_sp",
            "region": "SP",
            "site_id": "site_sp_centro",
            "machine_id": "machine_sp_01",
            "locker_id": "locker-sp-002",
            "signals": {
                "pickup_success_rate": 0.55,
                "expiration_rate": 0.22,
                "cancel_rate": 0.11,
                "avg_pickup_minutes": 95,
                "trend_direction": "worsening",
                "saturation_level": "high",
                "sample_size": 80,
            },
        },
    ]


# =========================================================
# CORE ENDPOINT
# =========================================================

@router.get("")
def get_pickup_health(
    entity_type: Optional[str] = Query(default="all"),
    tenant_id: Optional[str] = None,
    operator_id: Optional[str] = None,
    region: Optional[str] = None,
    site_id: Optional[str] = None,
    machine_id: Optional[str] = None,
    locker_id: Optional[str] = None,
    days: int = 7,
    limit: int = 100,
    include_ranking: bool = True,
    include_alerts: bool = True,
):
    # =========================================
    # TEMP: usar mock (trocar depois)
    # =========================================
    entities = _mock_entities()

    results = []

    for item in entities:
        signals = item["signals"]

        health = compute_health(signals)

        row = {
            "entity_type": item["entity_type"],
            "entity_id": item["entity_id"],
            "tenant_id": item["tenant_id"],
            "operator_id": item["operator_id"],
            "region": item["region"],
            "site_id": item["site_id"],
            "machine_id": item["machine_id"],
            "locker_id": item["locker_id"],
            "health_score": health["health_score"],
            "classification": health["classification"],
            "recommended_action": health["recommended_action"],
        }

        if include_alerts:
            row["alerts"] = health["alerts"]

        row["components"] = health["components"]
        row["signals"] = signals

        results.append(row)

    # =========================================
    # ORDER BY SCORE (ASC = pior primeiro)
    # =========================================
    results.sort(key=lambda x: x["health_score"])

    results = results[:limit]

    # =========================================
    # SUMMARY
    # =========================================
    summary = {
        "total_entities": len(results),
        "healthy_count": sum(1 for r in results if r["classification"] == "healthy"),
        "attention_count": sum(1 for r in results if r["classification"] == "attention"),
        "warning_count": sum(1 for r in results if r["classification"] == "warning"),
        "critical_count": sum(1 for r in results if r["classification"] == "critical"),
        "collapsed_count": sum(1 for r in results if r["classification"] == "collapsed"),
    }

    return {
        "ok": True,
        "window_days": days,
        "generated_at": _utc_now_iso(),
        "summary": summary,
        "ranking": results if include_ranking else [],
    }
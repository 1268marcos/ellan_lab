"""GET /intelligence/* — agregados ML para o frontend."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from app import db
from app.routers.ml_intelligence import intelligence_dashboard_mock

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

_LP = """SELECT DISTINCT ON (locker_id) locker_id, health_score, failure_probability, model_version, predicted_at
FROM ml_predictions_log ORDER BY locker_id, predicted_at DESC"""
_LF = """SELECT DISTINCT ON (locker_id) locker_id, battery_min_70d, door_failures_70d, feature_date
FROM ml_features_daily WHERE battery_min_70d IS NOT NULL ORDER BY locker_id, feature_date DESC"""


@router.get("/dashboard")
def intelligence_dashboard() -> dict[str, Any]:
    try:
        at_risk = db.fetch_all(
            f"""
            WITH lf AS ({_LF}), lp AS ({_LP})
            SELECT lf.locker_id, lp.health_score, lf.battery_min_70d AS battery_min, lf.door_failures_70d, lp.failure_probability
            FROM lf INNER JOIN lp ON lp.locker_id = lf.locker_id
            WHERE COALESCE(lp.health_score, 0) < 30 AND COALESCE(lf.battery_min_70d, 100) <= 20
            ORDER BY lp.health_score ASC LIMIT 200
            """
        )
        s7 = db.fetch_all(
            """
            SELECT (date_trunc('day', predicted_at AT TIME ZONE 'UTC'))::date AS d,
                   AVG(COALESCE(health_score, 0))::float AS avg_health_score
            FROM ml_predictions_log
            WHERE predicted_at >= (NOW() AT TIME ZONE 'UTC' - INTERVAL '7 days')
            GROUP BY 1 ORDER BY 1
            """
        )
        s30 = db.fetch_all(
            """
            SELECT (date_trunc('day', predicted_at AT TIME ZONE 'UTC'))::date AS d,
                   AVG(COALESCE(health_score, 0))::float AS avg_health_score
            FROM ml_predictions_log
            WHERE predicted_at >= (NOW() AT TIME ZONE 'UTC' - INTERVAL '30 days')
            GROUP BY 1 ORDER BY 1
            """
        )
        meta = db.fetch_one(
            "SELECT model_version, trained_at, metrics_json, status FROM ml_model_metadata WHERE status = 'ACTIVE' ORDER BY trained_at DESC LIMIT 1"
        )
        last_p = db.fetch_one("SELECT MAX(predicted_at) AS t FROM ml_predictions_log")
        top5 = db.fetch_all(
            f"WITH lp AS ({_LP}) SELECT * FROM lp ORDER BY health_score ASC NULLS LAST LIMIT 5"
        )
        acc = None
        if meta and isinstance(meta.get("metrics_json"), dict):
            acc = meta["metrics_json"].get("accuracy")
        return jsonable_encoder(
            {
                "at_risk_count": len(at_risk),
                "at_risk_lockers": at_risk,
                "avg_health_series": s30,
                "avg_health_score_series_7d": s7,
                "avg_health_score_series_30d": s30,
                "active_model": dict(meta) if meta else None,
                "last_prediction_at": last_p.get("t").isoformat() if last_p and last_p.get("t") else None,
                "active_accuracy": acc,
                "top5_worst_health": top5,
            }
        )
    except Exception as exc:
        logger.warning("intelligence /dashboard: fallback mock (%s)", exc)
        return intelligence_dashboard_mock()


@router.get("/models")
def intelligence_models() -> dict[str, Any]:
    rows = db.fetch_all(
        """
        SELECT model_version, trained_at, metrics_json, status
        FROM ml_model_metadata ORDER BY trained_at DESC LIMIT 40
        """
    )
    drift = None
    if len(rows) >= 2:
        m0, m1 = rows[0].get("metrics_json"), rows[1].get("metrics_json")
        if isinstance(m0, dict) and isinstance(m1, dict) and m0.get("accuracy") is not None and m1.get("accuracy") is not None:
            drift = float(m0["accuracy"]) - float(m1["accuracy"])
    return {"models": rows, "drift_delta_accuracy_vs_previous": drift}


@router.get("/at-risk")
def intelligence_at_risk(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    health_max: float = Query(30),
    region: str | None = None,
    operator_id: str | None = None,
) -> dict[str, Any]:
    off = (page - 1) * page_size
    wh = ["COALESCE(lp.health_score,0) < %s"]
    prm: list[Any] = [health_max]
    if region:
        wh.append("COALESCE(l.region, '') = %s")
        prm.append(region)
    if operator_id:
        wh.append("COALESCE(l.operator_id, '') = %s")
        prm.append(operator_id)
    wsql = " AND ".join(wh)
    q = f"""
        WITH lf AS ({_LF}), lp AS ({_LP})
        SELECT lp.locker_id, lp.health_score, lp.failure_probability, lf.battery_min_70d AS battery_min,
               lf.door_failures_70d, lp.predicted_at AS last_prediction_at, l.region, l.operator_id
        FROM lp LEFT JOIN lf ON lf.locker_id = lp.locker_id
        LEFT JOIN lockers l ON l.id = lp.locker_id
        WHERE {wsql}
        ORDER BY lp.health_score ASC NULLS LAST
        LIMIT %s OFFSET %s
    """
    rows = db.fetch_all(q, tuple(prm + [page_size, off]))
    cnt = db.fetch_one(
        f"WITH lf AS ({_LF}), lp AS ({_LP}) SELECT COUNT(*)::int AS c FROM lp LEFT JOIN lf ON lf.locker_id = lp.locker_id LEFT JOIN lockers l ON l.id = lp.locker_id WHERE {wsql}",
        tuple(prm),
    )
    return {"rows": rows, "page": page, "page_size": page_size, "total": int(cnt["c"]) if cnt else 0}


@router.get("/history")
def intelligence_history(days: int = Query(30, ge=1, le=120), locker_id: str | None = None) -> dict[str, Any]:
    lid = (locker_id or "").strip() or None
    win = "p.predicted_at >= (NOW() AT TIME ZONE 'UTC' - (%s * INTERVAL '1 day'))"
    lid_clause = " AND p.locker_id = %s" if lid else ""
    stacked = db.fetch_all(
        f"""
        SELECT (date_trunc('day', p.predicted_at AT TIME ZONE 'UTC'))::date AS d,
          SUM(CASE WHEN f.id IS NOT NULL AND (
            (p.failure_probability >= 0.5 AND COALESCE(f.failure_label_70d, f.failure_label_7d, 0) = 1)
            OR (p.failure_probability < 0.5 AND COALESCE(f.failure_label_70d, f.failure_label_7d, 0) = 0)
          ) THEN 1 ELSE 0 END)::int AS n_correct,
          SUM(CASE WHEN f.id IS NOT NULL AND NOT (
            (p.failure_probability >= 0.5 AND COALESCE(f.failure_label_70d, f.failure_label_7d, 0) = 1)
            OR (p.failure_probability < 0.5 AND COALESCE(f.failure_label_70d, f.failure_label_7d, 0) = 0)
          ) THEN 1 ELSE 0 END)::int AS n_wrong
        FROM ml_predictions_log p
        LEFT JOIN ml_features_daily f ON f.locker_id = p.locker_id
          AND f.feature_date = (p.predicted_at AT TIME ZONE 'UTC')::date
        WHERE {win}{lid_clause}
        GROUP BY 1 ORDER BY 1
        """,
        (days, lid) if lid else (days,),
    )
    tbl = db.fetch_all(
        f"""
        SELECT p.locker_id, p.predicted_at, p.failure_probability, p.health_score, p.model_version
        FROM ml_predictions_log p
        WHERE {win}{lid_clause}
        ORDER BY p.predicted_at DESC LIMIT 500
        """,
        (days, lid) if lid else (days,),
    )
    return {"stacked_daily": stacked, "predictions": tbl, "days": days}


@router.get("/pickup-fraud-hotspots")
def intelligence_pickup_fraud_hotspots(days: int = Query(30, ge=7, le=365)) -> dict[str, Any]:
    """Lockers com maior concentração de pickups marcados como fraude (fraud_flag)."""
    rows = db.fetch_all(
        """
        SELECT p.locker_id, COUNT(*)::int AS fraud_pickups
        FROM pickups p
        WHERE p.fraud_flag = true
          AND p.locker_id IS NOT NULL
          AND p.updated_at >= (NOW() AT TIME ZONE 'UTC' - (%s * INTERVAL '1 day'))
        GROUP BY p.locker_id
        ORDER BY fraud_pickups DESC
        LIMIT 80
        """,
        (days,),
    )
    total = db.fetch_one(
        """
        SELECT COUNT(*)::int AS c FROM pickups
        WHERE fraud_flag = true AND updated_at >= (NOW() AT TIME ZONE 'UTC' - (%s * INTERVAL '1 day'))
        """,
        (days,),
    )
    return {
        "days": days,
        "lockers": rows,
        "fraud_pickups_total_window": int(total["c"] or 0) if total else 0,
    }


@router.get("/ltv-scores")
def intelligence_ltv_scores(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    segment: str | None = None,
    campaign_prefix: str | None = None,
) -> dict[str, Any]:
    """Lista materializada em customer_ltv_scores (campanhas / OPS)."""
    off = (page - 1) * page_size
    wh: list[str] = ["1=1"]
    prm: list[Any] = []
    if segment:
        wh.append("segmento_cliente = %s")
        prm.append(segment.strip())
    if campaign_prefix:
        wh.append("campaign_segment LIKE %s")
        prm.append(campaign_prefix.strip() + "%")
    wsql = " AND ".join(wh)
    try:
        rows = db.fetch_all(
            f"""
            SELECT user_id, predicted_ltv_12m_cents, ltv_p05_cents, ltv_p95_cents,
                   churn_probability_30d, p_alive, segmento_cliente, campaign_segment,
                   features_90d, notification_engagement_90d, consent_marketing, consent_analytics,
                   model_version, scored_at
            FROM customer_ltv_scores
            WHERE {wsql}
            ORDER BY predicted_ltv_12m_cents DESC NULLS LAST
            LIMIT %s OFFSET %s
            """,
            tuple(prm + [page_size, off]),
        )
        cnt = db.fetch_one(f"SELECT COUNT(*)::int AS c FROM customer_ltv_scores WHERE {wsql}", tuple(prm))
        dist = db.fetch_all(
            """
            SELECT segmento_cliente, COUNT(*)::int AS n
            FROM customer_ltv_scores
            GROUP BY 1 ORDER BY n DESC
            """
        )
    except Exception as exc:
        logger.warning("ltv-scores query failed: %s", exc)
        if "customer_ltv_scores" in str(exc).lower() or "does not exist" in str(exc).lower():
            raise HTTPException(
                503,
                "Tabela customer_ltv_scores ausente ou inacessível. Aplique 02_docker/sql/customer_ltv_scores.sql e rode o treino com --materialize.",
            ) from exc
        raise
    return {
        "rows": rows,
        "page": page,
        "page_size": page_size,
        "total": int(cnt["c"]) if cnt else 0,
        "segment_distribution": dist,
    }


@router.get("/pickup-fraud-check/{pickup_id}")
def intelligence_pickup_fraud_score_readonly(pickup_id: str) -> dict[str, Any]:
    """Score sem bloquear (útil para painel OPS)."""
    from app.ml_fraud.score_pickup import score_pickup_realtime

    try:
        return score_pickup_realtime(pickup_id.strip())
    except FileNotFoundError as exc:
        raise HTTPException(503, "fraud model not trained") from exc
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc

"""POST /feedback/analyze e GET /feedback/ops-dashboard — NLP + persistência."""
from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from psycopg2 import ProgrammingError

from app import db
from app.auth_bearer import require_feedback_ops_user
from app.config import settings
from app.ml_nlp.sentiment_analyzer import analyze_text
from app.ml_nlp.topic_extractor import keyword_topics, lda_topics_batch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackAnalyzeBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)
    order_id: str | None = Field(None, max_length=64)
    rating: int | None = Field(None, ge=1, le=5)
    persist: bool = False
    source: str = Field("api_analyze", max_length=64)


def _table_exists() -> bool:
    row = db.fetch_one(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'customer_feedback'
        ) AS ok
        """
    )
    return bool(row and row.get("ok"))


def _tokenize_for_cloud(text: str) -> list[str]:
    t = (text or "").lower()
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
    return [w for w in t.split() if len(w) > 2]


def _record_negative_alert(
    *,
    user_id: str,
    feedback_id: str,
    order_id: str | None,
    rating: int,
    comment: str,
    sentiment_label: str,
) -> None:
    oid = (order_id or "").strip() or str(feedback_id)
    payload = {
        "feedback_id": feedback_id,
        "rating": rating,
        "sentiment_label": sentiment_label,
        "comment_preview": (comment or "")[:500],
    }
    try:
        db.execute(
            """
            INSERT INTO audit_logs (id, actor_id, actor_role, action, target_type, target_id, new_state)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                str(uuid.uuid4()),
                user_id,
                "ops_ml",
                "FEEDBACK_NEGATIVE_ALERT",
                "Order",
                oid[:36],
                json.dumps(payload, ensure_ascii=False),
            ),
        )
    except Exception:
        logger.exception("audit_logs FEEDBACK_NEGATIVE_ALERT failed")


@router.post("/analyze")
def post_feedback_analyze(
    body: FeedbackAnalyzeBody,
    user: dict[str, Any] = Depends(require_feedback_ops_user),
) -> dict[str, Any]:
    nlp = analyze_text(body.text)
    topics = keyword_topics(body.text, top_k=8)
    embedding_model = (
        "tfidf"
        if nlp.get("embedding_backend") == "tfidf"
        else (settings.feedback_embedding_model or "sentence-transformers")
    )

    out: dict[str, Any] = {
        "sentiment_label": nlp["sentiment_label"],
        "sentiment_score": float(nlp.get("sentiment_score") or 0.0),
        "user_intent": nlp["user_intent"],
        "topics": topics,
        "confidence": float(nlp.get("confidence") or 0.0),
        "intent_confidence": float(nlp.get("intent_confidence") or 0.0),
        "embedding_backend": nlp.get("embedding_backend"),
        "feedback_id": None,
        "alert_created": False,
    }

    if not body.persist:
        return out

    if not _table_exists():
        raise HTTPException(
            503,
            "Tabela customer_feedback ausente; aplique migrações do order_pickup_service (PostgreSQL).",
        )

    try:
        row = db.execute_returning(
            """
            INSERT INTO customer_feedback (
                order_id, rating, comment, sentiment_score, sentiment_label,
                topics, user_intent, source, embedding_model
            )
            VALUES (%s, %s, %s, %s, %s, %s::text[], %s, %s, %s)
            RETURNING id::text AS id
            """,
            (
                body.order_id,
                body.rating,
                body.text,
                out["sentiment_score"],
                out["sentiment_label"],
                topics,
                out["user_intent"],
                body.source[:64],
                embedding_model[:160],
            ),
        )
    except ProgrammingError as exc:
        logger.warning("customer_feedback insert failed: %s", exc)
        raise HTTPException(503, "Falha ao gravar feedback (schema).") from exc

    fid = row["id"] if row else None
    out["feedback_id"] = fid

    if fid and body.rating is not None and body.rating <= 2:
        _record_negative_alert(
            user_id=str(user["user_id"]),
            feedback_id=fid,
            order_id=body.order_id,
            rating=body.rating,
            comment=body.text,
            sentiment_label=str(out["sentiment_label"]),
        )
        try:
            db.execute(
                "UPDATE customer_feedback SET alert_notified_at = NOW() WHERE id = %s::uuid",
                (fid,),
            )
        except Exception:
            logger.exception("alert_notified_at update failed")
        out["alert_created"] = True

    return out


@router.get("/ops-dashboard")
def get_feedback_ops_dashboard(
    days: int = Query(30, ge=1, le=365),
    user: dict[str, Any] = Depends(require_feedback_ops_user),
) -> dict[str, Any]:
    del user  # auth only
    if not _table_exists():
        return {
            "ok": True,
            "table_ready": False,
            "nps": None,
            "nps_series": [],
            "sentiment_series": [],
            "word_cloud": [],
            "lda_topics": [],
            "recent": [],
            "negative_alerts_7d": 0,
        }

    d = max(1, min(days, 365))
    rows = db.fetch_all(
        """
        SELECT id::text AS id, order_id, rating, comment, sentiment_score, sentiment_label,
               topics, user_intent, created_at
        FROM customer_feedback
        WHERE created_at >= (NOW() AT TIME ZONE 'UTC' - (%s * INTERVAL '1 day'))
        ORDER BY created_at DESC
        LIMIT 5000
        """,
        (d,),
    )

    # NPS global na janela (ratings 1–5)
    ratings = [int(r["rating"]) for r in rows if r.get("rating") is not None]
    nps_val: float | None = None
    if ratings:
        promoters = sum(1 for x in ratings if x >= 5)
        detractors = sum(1 for x in ratings if x <= 2)
        n = len(ratings)
        nps_val = round(100.0 * (promoters / n - detractors / n), 1)

    # Série diária: NPS por dia (aprox.) + média sentiment_score
    by_day: dict[str, dict[str, Any]] = {}
    for r in rows:
        d = r.get("created_at")
        if d is None:
            continue
        key = d.date().isoformat() if hasattr(d, "date") else str(d)[:10]
        if key not in by_day:
            by_day[key] = {"ratings": [], "sentiments": [], "labels": []}
        if r.get("rating") is not None:
            by_day[key]["ratings"].append(int(r["rating"]))
        if r.get("sentiment_score") is not None:
            by_day[key]["sentiments"].append(float(r["sentiment_score"]))
        if r.get("sentiment_label"):
            by_day[key]["labels"].append(str(r["sentiment_label"]))

    nps_series: list[dict[str, Any]] = []
    sentiment_series: list[dict[str, Any]] = []
    for key in sorted(by_day.keys()):
        bd = by_day[key]
        rs = bd["ratings"]
        day_nps = None
        if rs:
            p = sum(1 for x in rs if x >= 5)
            dtr = sum(1 for x in rs if x <= 2)
            day_nps = round(100.0 * (p / len(rs) - dtr / len(rs)), 1)
        nps_series.append({"d": key, "nps": day_nps, "responses": len(rs)})
        avg_s = sum(bd["sentiments"]) / len(bd["sentiments"]) if bd["sentiments"] else None
        neg = sum(1 for x in bd["labels"] if x == "negative")
        pos = sum(1 for x in bd["labels"] if x == "positive")
        sentiment_series.append(
            {
                "d": key,
                "avg_sentiment_score": round(avg_s, 3) if avg_s is not None else None,
                "positive_count": pos,
                "negative_count": neg,
            }
        )

    # Nuvem de palavras (frequência global na janela)
    freq: dict[str, int] = {}
    for r in rows:
        for w in _tokenize_for_cloud(str(r.get("comment") or "")):
            freq[w] = freq.get(w, 0) + 1
    word_cloud = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:60]
    word_cloud_out = [{"text": k, "value": v} for k, v in word_cloud]

    comments = [str(r.get("comment") or "") for r in rows if r.get("comment")]
    lda: dict[str, Any] = {"ok": False, "topics": []}
    if len(comments) >= 3:
        lda = lda_topics_batch(
            comments[:400],
            n_topics=min(5, max(2, len(comments) // 15)),
        )

    neg_alerts = db.fetch_one(
        """
        SELECT COUNT(*)::int AS c
        FROM audit_logs
        WHERE action = 'FEEDBACK_NEGATIVE_ALERT'
          AND occurred_at >= (NOW() AT TIME ZONE 'UTC' - INTERVAL '7 days')
        """
    )
    neg_c = int(neg_alerts["c"]) if neg_alerts and neg_alerts.get("c") is not None else 0

    return {
        "ok": True,
        "table_ready": True,
        "days": days,
        "nps": nps_val,
        "nps_series": nps_series,
        "sentiment_series": sentiment_series,
        "word_cloud": word_cloud_out,
        "lda_topics": lda,
        "recent": rows[:40],
        "negative_alerts_7d": neg_c,
    }

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.fiscal_global import FiscalIntegrationReadiness


def list_readiness(db: Session, band: str | None = None, limit: int = 200) -> list[FiscalIntegrationReadiness]:
    q = db.query(FiscalIntegrationReadiness)
    if band:
        q = q.filter(FiscalIntegrationReadiness.readiness_band == band.upper())
    return q.order_by(FiscalIntegrationReadiness.score_total.desc()).limit(limit).all()


def readiness_to_dict(row: FiscalIntegrationReadiness) -> dict:
    try:
        blockers = json.loads(row.blockers_json or "[]")
    except json.JSONDecodeError:
        blockers = []
    return {
        "issuer_id": row.issuer_id,
        "issuer_code": row.issuer_code,
        "country": row.country,
        "score_total": float(row.score_total),
        "score_certificates": float(row.score_certificates),
        "score_api": float(row.score_api),
        "score_contingency": float(row.score_contingency),
        "readiness_band": row.readiness_band,
        "blockers": blockers,
        "computed_at": row.computed_at.isoformat() if row.computed_at else None,
    }

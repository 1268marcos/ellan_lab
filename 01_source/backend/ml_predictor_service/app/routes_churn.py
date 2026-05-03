"""GET /ops/partners/churn-risk — risco de churn por parceiro logístico."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.ml_churn.predict_churn_risk import predict_all_partners, predict_partner_risk

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ops/partners", tags=["partners-churn"])


@router.get("/churn-risk")
def ops_partners_churn_risk(
    partner_id: str | None = None,
    min_risk: float = Query(70, ge=0, le=100),
) -> dict[str, Any]:
    try:
        if partner_id:
            row = predict_partner_risk(partner_id.strip())
            return {"partners": [row], "high_risk": [row] if row["risk_score"] >= min_risk else []}
        all_rows = predict_all_partners()
        high = [r for r in all_rows if r["risk_score"] >= min_risk]
        return {"partners": all_rows, "high_risk": high}
    except FileNotFoundError as e:
        logger.warning("churn model missing: %s", e)
        raise HTTPException(503, "churn model not trained; run train_churn_model") from e
    except ValueError as e:
        raise HTTPException(404, str(e)) from e

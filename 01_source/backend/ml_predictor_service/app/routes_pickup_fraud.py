"""POST /pickups/{pickup_id}/fraud-check — detecção ML + bloqueio opcional."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

from app.ml_fraud.score_pickup import apply_fraud_block_and_alert, score_pickup_realtime

logger = logging.getLogger(__name__)
router = APIRouter(tags=["pickup-fraud"])


class FraudCheckBody(BaseModel):
    apply_block: bool = Field(True, description="Se true e score≥0.9, marca fraud_flag e audit_logs")


@router.post("/pickups/{pickup_id}/fraud-check")
def post_pickup_fraud_check(
    pickup_id: str,
    body: FraudCheckBody = Body(default_factory=lambda: FraudCheckBody()),
) -> dict[str, Any]:
    apply_block = body.apply_block
    pid = pickup_id.strip()
    try:
        out = score_pickup_realtime(pid)
    except FileNotFoundError as exc:
        logger.warning("fraud model missing: %s", exc)
        raise HTTPException(503, "fraud model not trained; run python -m app.ml_fraud.train_fraud_models") from exc
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:
        logger.exception("fraud-check failed")
        raise HTTPException(500, str(exc)) from exc

    actions: list[str] = []
    if apply_block and out.get("should_block"):
        block = apply_fraud_block_and_alert(
            pid,
            float(out["anomaly_score"]),
            "ensemble_iforest_autoencoder",
        )
        out["block_result"] = block
        if block.get("fraud_flag_set"):
            actions.extend(["fraud_flag_set", "audit_logged"])
        elif block.get("blocked") is False and out["should_block"]:
            actions.append("already_flagged_or_update_skipped")
    else:
        out["block_result"] = {"blocked": False, "skipped": not apply_block}
    out["actions_taken"] = actions
    return out

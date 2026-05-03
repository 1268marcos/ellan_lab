"""Endpoints /pricing/* — sugestão dinâmica, feedback do bandit e simulação A/B."""
from __future__ import annotations

import hashlib
import logging
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app import db
from app.ml_pricing.ab_testing import assign_ab_variant, simulate_policy_comparison
from app.ml_pricing.price_suggester import bandit_feedback, suggest_dynamic_pricing

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pricing", tags=["pricing-ml"])


class DynamicSuggestIn(BaseModel):
    locker_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1, description="SKU / product_id do catálogo")
    session_id: str | None = Field(None, description="Para atribuição A/B estável")
    apply_proxy_learning: bool = False
    persist_bandit: bool = False
    random_seed: int | None = None


class BanditFeedbackIn(BaseModel):
    locker_id: str
    product_id: str
    arm_index: int = Field(..., ge=0, le=8)
    reward: float = Field(..., description="Conversão 0/1 ou log-receita normalizada")
    persist: bool = True


class AbSimulateIn(BaseModel):
    n_steps: int = Field(500, ge=50, le=5000)
    n_runs: int = Field(80, ge=10, le=500)
    seed: int = 42


@router.post("/dynamic-suggest")
def post_dynamic_suggest(body: DynamicSuggestIn) -> dict[str, Any]:
    lid = body.locker_id.strip()
    pid = body.product_id.strip()
    row = db.fetch_one("SELECT id FROM lockers WHERE id = %s LIMIT 1", (lid,))
    if not row:
        raise HTTPException(404, "locker not found")
    if body.random_seed is not None:
        seed = int(body.random_seed)
    else:
        h = hashlib.sha256(f"{lid}|{pid}|{body.session_id or ''}".encode()).hexdigest()
        seed = int(h[:8], 16) % (2**31)
    rng = np.random.default_rng(seed)
    try:
        out = suggest_dynamic_pricing(
            lid,
            pid,
            rng=rng,
            persist_state=body.persist_bandit,
            apply_proxy_learning=body.apply_proxy_learning,
        )
    except Exception as exc:
        logger.exception("dynamic-suggest failed")
        raise HTTPException(500, str(exc)) from exc
    unit = body.session_id or f"{lid}:{pid}"
    out["ab_variant"] = assign_ab_variant(unit, experiment_salt="dynamic_pricing_v1")
    out["ab_note"] = "treatment pode aplicar sugestão do modelo; control mantém preço base de catálogo/regra."
    return out


@router.post("/bandit-feedback")
def post_bandit_feedback(body: BanditFeedbackIn) -> dict[str, Any]:
    try:
        return bandit_feedback(
            body.locker_id.strip(),
            body.product_id.strip(),
            body.arm_index,
            body.reward,
            persist=body.persist,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        logger.exception("bandit-feedback failed")
        raise HTTPException(500, str(exc)) from exc


@router.post("/ab/simulate")
def post_ab_simulate(body: AbSimulateIn) -> dict[str, Any]:
    return simulate_policy_comparison(n_steps=body.n_steps, n_runs=body.n_runs, seed=body.seed)

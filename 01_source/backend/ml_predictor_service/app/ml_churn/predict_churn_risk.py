"""Carrega churn_model.pkl e devolve risk_score 0–100 (probabilidade de churn * 100)."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.config import settings
from app.ml_churn.feature_frame import FEATURE_COLS, load_training_frame

logger = logging.getLogger(__name__)


def _bundle():
    p = Path(settings.churn_model_path)
    if not p.exists():
        raise FileNotFoundError(f"modelo não encontrado: {p}")
    return joblib.load(p)


def predict_partner_risk(partner_id: str) -> dict[str, Any]:
    b = _bundle()
    clf = b["model"]
    feats = b.get("features") or FEATURE_COLS
    df = load_training_frame()
    row = df[df["partner_id"] == partner_id]
    if row.empty:
        raise ValueError(f"parceiro sem features: {partner_id}")
    r = row.iloc[0]
    X = r[feats].values.astype(np.float32).reshape(1, -1)
    p = float(clf.predict_proba(X)[0, 1])
    return {
        "partner_id": partner_id,
        "name": r.get("name"),
        "code": r.get("code"),
        "active": bool(r.get("active")) if r.get("active") is not None else True,
        "churn_probability": p,
        "risk_score": round(p * 100.0, 2),
    }


def predict_all_partners() -> list[dict[str, Any]]:
    """Todos os parceiros com linha de features (ativos e inativos na base)."""
    b = _bundle()
    clf = b["model"]
    feats = b.get("features") or FEATURE_COLS
    df = load_training_frame()
    out = []
    for _, r in df.iterrows():
        X = np.asarray(r[feats].tolist(), dtype=np.float32).reshape(1, -1)
        p = float(clf.predict_proba(X)[0, 1])
        out.append(
            {
                "partner_id": r["partner_id"],
                "name": r.get("name"),
                "code": r.get("code"),
                "active": bool(r.get("active")) if r.get("active") is not None else True,
                "churn_probability": p,
                "risk_score": round(p * 100.0, 2),
            }
        )
    out.sort(key=lambda x: -x["risk_score"])
    logger.info("churn predict_all n=%s", len(out))
    return out

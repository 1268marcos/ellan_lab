"""Treina XGBoost balanceado para churn de logistics_partners; grava artifacts/churn_model.pkl."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from app.config import settings
from app.ml_churn.feature_frame import FEATURE_COLS, load_training_frame

logger = logging.getLogger(__name__)


def train_and_save() -> dict:
    df = load_training_frame()
    if len(df) < 20:
        raise RuntimeError(f"poucos parceiros para treino: {len(df)}")
    X = df[FEATURE_COLS].values.astype(np.float32)
    y = df["churn_next_30d"].astype(np.int32).values
    pos = max(1, int(y.sum()))
    neg = max(1, len(y) - pos)
    spw = neg / pos
    strat = y if len(np.unique(y)) > 1 else None
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=strat)
    clf = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        scale_pos_weight=spw,
        eval_metric="logloss",
        random_state=42,
    )
    clf.fit(X_tr, y_tr)
    from sklearn.metrics import average_precision_score, roc_auc_score

    proba = clf.predict_proba(X_te)[:, 1]
    metrics = {"n": len(df), "positives": int(pos)}
    if len(np.unique(y_te)) > 1:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_te, proba))
            metrics["pr_auc"] = float(average_precision_score(y_te, proba))
        except ValueError:
            pass
    path = Path(settings.churn_model_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {"model": clf, "features": FEATURE_COLS, "metrics": metrics}
    joblib.dump(bundle, path)
    (path.parent / "churn_model.meta.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    logger.info("churn model saved path=%s metrics=%s", path, metrics)
    return {"path": str(path), "metrics": metrics}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(train_and_save())

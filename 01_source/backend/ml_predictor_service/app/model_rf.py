from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score

FEATURE_COLS = [
    "temperature_mean",
    "humidity_mean",
    "battery_min",
    "door_failures_7d",
    "usage_events_7d",
    "uptime_hours_7d",
]


def train_from_rows(rows: list[dict[str, Any]]) -> tuple[RandomForestClassifier, dict[str, float]]:
    if len(rows) < 10:
        raise ValueError("need at least 10 training rows")
    X = np.array([[float(r[c] or 0) for c in FEATURE_COLS] for r in rows], dtype=np.float64)
    y = np.array([int(r["failure_label_7d"]) for r in rows], dtype=np.int64)
    if len(np.unique(y)) < 2:
        raise ValueError("training data must include both failure_label_7d 0 and 1")
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X, y)
    pred = clf.predict(X)
    metrics = {
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "n_samples": float(len(rows)),
    }
    return clf, metrics


def save_model(clf: RandomForestClassifier, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"clf": clf, "features": FEATURE_COLS}, path)


def load_model(path: Path) -> RandomForestClassifier:
    data = joblib.load(path)
    return data["clf"]


def predict_failure_prob(clf: RandomForestClassifier, row: dict[str, Any]) -> float:
    x = np.array([[float(row.get(c) or 0) for c in FEATURE_COLS]], dtype=np.float64)
    if hasattr(clf, "predict_proba"):
        return float(clf.predict_proba(x)[0, 1])
    return float(clf.predict(x)[0])


def health_score(prob: float) -> float:
    return float(max(0.0, min(100.0, round(100.0 * (1.0 - prob), 2))))


def new_model_version() -> str:
    return datetime.now(timezone.utc).strftime("rf-%Y%m%dT%H%M%SZ")

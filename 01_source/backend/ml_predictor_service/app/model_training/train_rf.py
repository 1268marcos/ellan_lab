"""Treina RandomForest a partir de ml_features_daily (últimos 90 dias)."""
from __future__ import annotations

import argparse
import logging
import math
from datetime import date, datetime, timedelta, timezone
from collections import Counter

import numpy as np
import psycopg2.extensions
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from app.db_ml import ml_connection
from app.model_training.save_model import save_trained_model

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Colunas que existem no schema
FEATURE_COLS = [
    "temperature_mean",
    "humidity_mean", 
    "battery_min",
    "door_failures_7d",
    "usage_events_7d",
    "uptime_hours_7d",
]
TARGET = "failure_label_7d"

MIN_SAMPLES_PER_LOCKER = 30


def _fetch_frame(
    conn: psycopg2.extensions.connection, start: date
) -> tuple[list[tuple], list[str]]:
    cols = ["locker_id", "feature_date", *FEATURE_COLS, TARGET]
    sel = ", ".join(f"m.{c}" for c in cols)
    
    # CORRIGIDO: Usa os nomes corretos das colunas no WHERE
    q = f"""
        SELECT {sel}
        FROM public.ml_features_daily m
        WHERE m.feature_date >= %s::date
          AND m.failure_label_7d IS NOT NULL
          AND m.temperature_mean IS NOT NULL
          AND m.humidity_mean IS NOT NULL
          AND m.battery_min IS NOT NULL
          AND m.door_failures_7d IS NOT NULL
          AND m.usage_events_7d IS NOT NULL
          AND m.uptime_hours_7d IS NOT NULL
    """
    with conn.cursor() as cur:
        cur.execute(q, (start.isoformat(),))
        rows = cur.fetchall()
    return rows, cols


def _filter_lockers(rows: list[tuple], col_names: list[str]) -> list[tuple]:
    li = col_names.index("locker_id")
    counts = Counter(r[li] for r in rows)
    ok = {k for k, v in counts.items() if v >= MIN_SAMPLES_PER_LOCKER}
    return [r for r in rows if r[li] in ok]


def train(rows: list[tuple], col_names: list[str]) -> tuple[RandomForestClassifier, dict]:
    idx = {n: i for i, n in enumerate(col_names)}
    X = np.array([[float(r[idx[c]]) if r[idx[c]] is not None else 0.0 for c in FEATURE_COLS] for r in rows])
    y = np.array([int(r[idx[TARGET]]) for r in rows], dtype=np.int32)
    
    if len(np.unique(y)) < 2:
        raise RuntimeError("Target tem uma única classe; não é possível treinar.")
    
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=15,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_tr, y_tr)
    
    proba = clf.predict_proba(X_te)[:, 1]
    pred = (proba >= 0.5).astype(np.int32)
    
    acc = float((pred == y_te).mean())
    prec = float(precision_score(y_te, pred, zero_division=0))
    rec = float(recall_score(y_te, pred, zero_division=0))
    f1 = float(f1_score(y_te, pred, zero_division=0))
    
    try:
        roc = float(roc_auc_score(y_te, proba))
    except ValueError:
        roc = float("nan")
    roc_j = None if isinstance(roc, float) and math.isnan(roc) else roc
    
    metrics = {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "roc_auc": roc_j,
        "n_rows": len(rows),
        "n_features": len(FEATURE_COLS),
    }
    
    log.info(
        "accuracy=%.4f precision=%.4f recall=%.4f f1=%.4f roc_auc=%s",
        acc, prec, rec, f1,
        "nan" if roc_j is None else f"{roc_j:.4f}",
    )
    return clf, metrics


def run_sklearn_training(
    days: int = 90, model_dir: str | None = None
) -> dict[str, object]:
    """API/CLI: treina RF, grava pkl + metadata; retorna métricas e versão."""
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days - 1)
    
    with ml_connection() as conn:
        rows, cols = _fetch_frame(conn, start)
    
    rows = _filter_lockers(rows, cols)
    
    if len(rows) < 50:
        raise RuntimeError(
            f"Poucos dados após filtro (>={MIN_SAMPLES_PER_LOCKER}/locker): {len(rows)}"
        )
    
    model, metrics = train(rows, cols)
    plain = {k: (v.item() if hasattr(v, "item") else v) for k, v in metrics.items()}
    ver = save_trained_model(model, plain, model_dir=model_dir)
    log.info("model_version=%s", ver)
    return {"model_version": ver, "metrics": plain, "n_rows": len(rows)}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--model-dir", type=str, default=None)
    args = p.parse_args()
    run_sklearn_training(days=args.days, model_dir=args.model_dir)


if __name__ == "__main__":
    main()
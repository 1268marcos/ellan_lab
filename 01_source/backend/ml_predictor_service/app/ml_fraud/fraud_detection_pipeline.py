"""Treino ensemble: Isolation Forest + Autoencoder (Keras) + percentis dinâmicos."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.config import settings
from app.ml_fraud.feature_pickup import FEATURE_NAMES, training_rows

logger = logging.getLogger(__name__)


def _build_autoencoder(input_dim: int):
    from tensorflow import keras
    from tensorflow.keras import layers

    h = max(8, input_dim // 2)
    z = max(4, input_dim // 4)
    inp = layers.Input(shape=(input_dim,))
    x = layers.Dense(h, activation="relu")(inp)
    x = layers.Dropout(0.15)(x)
    x = layers.Dense(z, activation="relu")(x)
    x = layers.Dense(h, activation="relu")(x)
    out = layers.Dense(input_dim, activation="linear")(x)
    m = keras.Model(inp, out)
    m.compile(optimizer=keras.optimizers.Adam(0.002), loss="mse")
    return m


def _norm_train(values: np.ndarray) -> tuple[np.ndarray, float, float]:
    p5, p95 = np.percentile(values, 5), np.percentile(values, 95)
    span = max(p95 - p5, 1e-9)
    return np.clip((values - p5) / span, 0.0, 1.0), float(p5), float(p95)


def train_and_save(epochs: int = 18, batch_size: int = 64) -> dict[str, Any]:
    X, pids = training_rows(limit=12000)
    if len(X) < 80:
        rng = np.random.default_rng(42)
        X = rng.lognormal(0, 0.5, (400, len(FEATURE_NAMES))).astype(np.float64)
        X[:, 0] = rng.uniform(0, 120, size=400)
        pids = [f"syn-{i}" for i in range(400)]
        logger.warning("poucos pickups reais; treino com %s linhas sintéticas", len(X))

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    iforest = IsolationForest(
        n_estimators=200,
        contamination=0.06,
        random_state=42,
        n_jobs=-1,
    )
    iforest.fit(Xs)
    raw_iso = -iforest.decision_function(Xs).astype(np.float64)
    n_iso, p_iso_5, p_iso_95 = _norm_train(raw_iso)

    ae = _build_autoencoder(Xs.shape[1])
    ae.fit(Xs, Xs, epochs=epochs, batch_size=min(batch_size, len(Xs)), verbose=0, validation_split=0.1)
    recon = ae.predict(Xs, verbose=0)
    raw_ae = np.mean((Xs - recon) ** 2, axis=1).astype(np.float64)
    n_ae, p_ae_5, p_ae_95 = _norm_train(raw_ae)

    ens = 0.45 * n_iso + 0.55 * n_ae
    calibration_p95 = float(np.percentile(ens, 95))

    bundle = {
        "feature_names": FEATURE_NAMES,
        "scaler": scaler,
        "iforest": iforest,
        "p_iso_5": p_iso_5,
        "p_iso_95": p_iso_95,
        "p_ae_5": p_ae_5,
        "p_ae_95": p_ae_95,
        "calibration_p95": calibration_p95,
        "train_n": len(X),
        "train_pickup_sample": pids[:5],
    }

    out_dir = Path(settings.fraud_model_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ae_path = (out_dir / "fraud_autoencoder.keras").resolve()
    ae.save(ae_path)
    bundle["ae_path"] = str(ae_path)

    joblib.dump(bundle, settings.fraud_model_bundle_path)
    meta = {
        "bundle_path": settings.fraud_model_bundle_path,
        "ae_path": str(ae_path),
        "n_features": len(FEATURE_NAMES),
        "train_n": len(X),
        "ensemble_score_percentile_95_train": calibration_p95,
    }
    Path(settings.fraud_model_meta_path).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    logger.info("fraud model saved n=%s -> %s", len(X), settings.fraud_model_bundle_path)
    return meta


def load_bundle() -> dict[str, Any]:
    from tensorflow import keras

    p = Path(settings.fraud_model_bundle_path)
    if not p.exists():
        raise FileNotFoundError(f"bundle não encontrado: {p}")
    b = joblib.load(p)
    ae_path = Path(b["ae_path"])
    if not ae_path.is_absolute():
        ae_path = Path(settings.fraud_model_dir) / ae_path.name
    b["ae"] = keras.models.load_model(str(ae_path), compile=False)
    b["ae"].compile(optimizer="adam", loss="mse")
    return b

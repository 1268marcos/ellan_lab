"""LSTM (Keras) para ocupação futura: 168h × features → 24h de occ_rate."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from app.config import settings
from app.ml_demand.series_builder import HORIZON, N_FEATURES, SEQ_LEN, collect_training_arrays, synthetic_training_data

logger = logging.getLogger(__name__)


def _keras():
    try:
        from tensorflow import keras  # noqa: WPS433
    except ImportError as exc:
        raise ImportError("tensorflow não instalado; pip install tensorflow") from exc
    return keras


def build_model() -> Any:
    keras = _keras()
    m = keras.Sequential(
        [
            keras.layers.Input(shape=(SEQ_LEN, N_FEATURES)),
            keras.layers.LSTM(64, return_sequences=True),
            keras.layers.Dropout(0.2),
            keras.layers.LSTM(64, return_sequences=False),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(HORIZON),
        ],
        name="locker_occupancy_lstm",
    )
    m.compile(optimizer=keras.optimizers.Adam(0.001), loss="mse", metrics=["mae"])
    return m


def _scale_xy(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, StandardScaler, StandardScaler]:
    ns, _, f = X.shape
    x_sc = StandardScaler()
    Xf = X.reshape(-1, f)
    Xs = x_sc.fit_transform(Xf).reshape(ns, SEQ_LEN, f)
    y_sc = StandardScaler()
    ys = y_sc.fit_transform(y.reshape(-1, 1)).reshape(ns, HORIZON)
    return Xs.astype(np.float32), ys.astype(np.float32), x_sc, y_sc


def train_and_save(epochs: int = 25, batch_size: int = 32) -> dict[str, Any]:
    X, y = collect_training_arrays()
    if len(X) < 64:
        logger.warning("poucos dados reais (%s); usando sintético para bootstrap", len(X))
        X_syn, y_syn = synthetic_training_data(n=512)
        if len(X) > 0:
            X = np.concatenate([X, X_syn], axis=0)
            y = np.concatenate([y, y_syn], axis=0)
        else:
            X, y = X_syn, y_syn

    Xs, ys, x_sc, y_sc = _scale_xy(X, y)
    X_tr, X_va, y_tr, y_va = train_test_split(Xs, ys, test_size=0.15, random_state=42)

    model = build_model()
    keras = _keras()
    cb = keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True, monitor="val_loss")
    hist = model.fit(
        X_tr,
        y_tr,
        validation_data=(X_va, y_va),
        epochs=epochs,
        batch_size=batch_size,
        verbose=0,
        callbacks=[cb],
    )
    loss = float(hist.history["val_loss"][-1]) if hist.history.get("val_loss") else None
    mae = float(hist.history["val_mae"][-1]) if hist.history.get("val_mae") else None

    out_path = Path(settings.lstm_occupancy_model_path)
    meta_path = Path(settings.lstm_occupancy_meta_path)
    scal_path = Path(settings.lstm_occupancy_scalers_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(out_path)
    joblib.dump({"x_scaler": x_sc, "y_scaler": y_sc}, scal_path)
    meta = {
        "model_path": str(out_path),
        "seq_len": SEQ_LEN,
        "horizon": HORIZON,
        "n_features": N_FEATURES,
        "val_loss": loss,
        "val_mae_scaled": mae,
        "n_train_windows": len(X),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    logger.info("LSTM salvo em %s (n=%s)", out_path, len(X))
    return meta


def load_bundle() -> tuple[Any, StandardScaler, StandardScaler, dict]:
    from tensorflow import keras  # noqa: WPS433

    mp = Path(settings.lstm_occupancy_model_path)
    sp = Path(settings.lstm_occupancy_scalers_path)
    meta = {}
    mpath = Path(settings.lstm_occupancy_meta_path)
    if mpath.exists():
        meta = json.loads(mpath.read_text(encoding="utf-8"))
    if not mp.exists() or not sp.exists():
        raise FileNotFoundError("modelo LSTM não treinado")
    bundle = joblib.load(sp)
    model = keras.models.load_model(mp, compile=False)
    model.compile(optimizer=keras.optimizers.Adam(0.001), loss="mse", metrics=["mae"])
    return model, bundle["x_scaler"], bundle["y_scaler"], meta

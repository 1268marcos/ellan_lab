"""Random Forest para estimar travel_time (min) a partir de distância e clusters."""
from __future__ import annotations

import math
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from app.config import settings

AVG_SPEED_KMH = 28.0


def haversine_km_matrix(coords: np.ndarray) -> np.ndarray:
    """coords (n,2) lat,lon → matriz (n,n) km."""
    n = coords.shape[0]
    out = np.zeros((n, n), dtype=np.float64)
    r = 6371.0
    rad = np.radians(coords)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            dlat = rad[j, 0] - rad[i, 0]
            dlon = rad[j, 1] - rad[i, 1]
            a = math.sin(dlat / 2) ** 2 + math.cos(rad[i, 0]) * math.cos(rad[j, 0]) * math.sin(dlon / 2) ** 2
            out[i, j] = 2 * r * math.asin(min(1.0, math.sqrt(a)))
    return out


def ensure_travel_rf() -> RandomForestRegressor:
    """Modelo global (treino sintético) persistido em disco."""
    p = Path(settings.routing_travel_rf_path)
    if p.exists():
        return joblib.load(p)
    rng = np.random.default_rng(42)
    X: list[list[float]] = []
    y: list[float] = []
    for _ in range(4000):
        d = float(rng.uniform(0.2, 150.0))
        c1 = float(rng.integers(0, 16))
        c2 = float(rng.integers(0, 16))
        base = (d / AVG_SPEED_KMH) * 60.0 * float(rng.lognormal(0.0, 0.1))
        X.append([d, c1, c2, math.log1p(d)])
        y.append(max(1.0, base))
    rf = RandomForestRegressor(n_estimators=100, max_depth=14, random_state=42, n_jobs=-1)
    rf.fit(np.array(X), np.array(y))
    p.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(rf, p)
    return rf


def build_time_matrix_minutes(
    coords: np.ndarray,
    cluster_ids: np.ndarray,
    service_minutes: np.ndarray,
    rf: RandomForestRegressor | None,
) -> np.ndarray:
    """
    mat[i,j] = tempo viagem i→j + serviço ao chegar em j (min).
    Depot j=0 sem serviço extra.
    """
    n = coords.shape[0]
    dist = haversine_km_matrix(coords)
    mat = np.zeros((n, n), dtype=np.float64)
    model = rf or ensure_travel_rf()
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            d = max(0.0, float(dist[i, j]))
            x = np.array([[d, float(cluster_ids[i]), float(cluster_ids[j]), math.log1p(d)]], dtype=np.float64)
            travel = max(1.0, float(model.predict(x)[0]))
            svc = float(service_minutes[j])
            mat[i, j] = travel + svc
    return mat

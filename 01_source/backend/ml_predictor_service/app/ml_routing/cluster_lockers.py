"""K-means em coordenadas (lat/lon) para agrupar lockers geograficamente."""
from __future__ import annotations

import math
from typing import Any

import numpy as np
from sklearn.cluster import KMeans


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 6371.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dphi = math.radians(b[0] - a[0])
    dl = math.radians(b[1] - a[1])
    x = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(x)))


def auto_k(n_points: int, max_k: int = 12) -> int:
    if n_points <= 2:
        return 1
    return max(2, min(max_k, int(round(math.sqrt(max(n_points, 4))))))


def cluster_lockers_coords(coords: np.ndarray, k: int | None = None, random_state: int = 42) -> np.ndarray:
    """
    coords: shape (n, 2) lat, lon em graus.
    Retorna labels int 0..k-1 (n>=1).
    """
    if coords.size == 0:
        return np.array([], dtype=np.int32)
    n = coords.shape[0]
    if n == 1:
        return np.zeros(1, dtype=np.int32)
    k_use = k or auto_k(n)
    k_use = max(1, min(k_use, n))
    km = KMeans(n_clusters=k_use, random_state=random_state, n_init=10)
    return km.fit_predict(coords).astype(np.int32)


def cluster_intra_group_diameter_km(coords: np.ndarray, labels: np.ndarray) -> dict[int, float]:
    """Diâmetro aproximado (km) por cluster — diagnóstico."""
    out: dict[int, float] = {}
    for lab in np.unique(labels):
        pts = coords[labels == lab]
        if len(pts) < 2:
            out[int(lab)] = 0.0
            continue
        maxd = 0.0
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                maxd = max(maxd, _haversine_km((pts[i][0], pts[i][1]), (pts[j][0], pts[j][1])))
        out[int(lab)] = maxd
    return out


def summarize_clusters(locker_ids: list[str], coords: np.ndarray, labels: np.ndarray) -> list[dict[str, Any]]:
    rows = []
    for i, lid in enumerate(locker_ids):
        rows.append({"locker_id": lid, "cluster": int(labels[i]), "lat": float(coords[i, 0]), "lon": float(coords[i, 1])})
    return rows

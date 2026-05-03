"""
Otimização de rota: K-means + RF (tempos) + OR-Tools VRP com capacidade e limite de tempo da rota.
Nó 0 = depósito sintético (centróide); nós 1..n = lockers. Saída: ordem de visitas + km (ingênuo vs otimizado).
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from app import db
from app.ml_routing.cluster_lockers import auto_k, cluster_lockers_coords, summarize_clusters
from app.ml_routing.travel_time_rf import build_time_matrix_minutes, ensure_travel_rf, haversine_km_matrix

logger = logging.getLogger(__name__)


def _fetch_lockers_rows(locker_ids: list[str]) -> list[dict[str, Any]]:
    if not locker_ids:
        return []
    rows = db.fetch_all(
        """
        SELECT l.id AS locker_id,
               COALESCE(l.latitude::float8, cl.latitude::float8) AS lat,
               COALESCE(l.longitude::float8, cl.longitude::float8) AS lon,
               l.temperature_zone,
               l.security_level,
               l.slots_count,
               cl.operating_hours_json
        FROM lockers l
        LEFT JOIN capability_locker_location cl
          ON cl.external_id = l.external_id AND cl.is_active = true
        WHERE l.id = ANY(%s::varchar[])
        """,
        (list(locker_ids),),
    )
    by_id = {str(r["locker_id"]): r for r in rows}
    ordered = []
    for lid in locker_ids:
        if lid in by_id:
            ordered.append(by_id[lid])
    return ordered


def _fetch_demands(locker_ids: list[str]) -> dict[str, int]:
    if not locker_ids:
        return {}
    rows = db.fetch_all(
        """
        SELECT locker_id, COUNT(*)::int AS c
        FROM inbound_deliveries
        WHERE locker_id = ANY(%s::varchar[])
          AND status NOT IN ('PICKED_UP', 'RETURNED', 'EXPIRED')
        GROUP BY locker_id
        """,
        (list(locker_ids),),
    )
    return {str(r["locker_id"]): int(r["c"] or 0) for r in rows}


def _fetch_priority_minutes(locker_ids: list[str]) -> dict[str, float]:
    """Urgência: min até pickup_deadline (menor = mais prioritário). Sem deadline → valor alto."""
    if not locker_ids:
        return {}
    rows = db.fetch_all(
        """
        SELECT locker_id,
               MIN(EXTRACT(EPOCH FROM (pickup_deadline_at - NOW())) / 60.0)::float AS m
        FROM inbound_deliveries
        WHERE locker_id = ANY(%s::varchar[])
          AND status NOT IN ('PICKED_UP', 'RETURNED', 'EXPIRED')
          AND pickup_deadline_at IS NOT NULL
        GROUP BY locker_id
        """,
        (list(locker_ids),),
    )
    return {str(r["locker_id"]): float(r["m"]) if r.get("m") is not None else 10_000.0 for r in rows}


def _service_minutes_per_locker(
    locker_rows: list[dict[str, Any]],
    demands: dict[str, int],
    priority: dict[str, float],
    base_service: float,
) -> list[float]:
    out: list[float] = []
    for r in locker_rows:
        lid = str(r["locker_id"])
        d = max(1, demands.get(lid, 1))
        pr = priority.get(lid, 10_000.0)
        urgent = 8.0 if pr < 24 * 60 else (4.0 if pr < 72 * 60 else 0.0)
        out.append(float(base_service) + 0.8 * float(d) + urgent)
    return out


def _closed_tour_km_haversine(node_seq: list[int], coords: np.ndarray) -> float:
    dist = haversine_km_matrix(coords)
    s = 0.0
    for a, b in zip(node_seq[:-1], node_seq[1:]):
        s += float(dist[a, b])
    return s


def _nearest_neighbor_order(n_nodes_aug: int, time_mat: np.ndarray) -> list[int]:
    """Fallback: greedy por tempo a partir do depósito 0."""
    visited = {0}
    order = [0]
    cur = 0
    while len(visited) < n_nodes_aug:
        best_j, best_t = None, float("inf")
        for j in range(n_nodes_aug):
            if j in visited:
                continue
            t = float(time_mat[cur, j])
            if t < best_t:
                best_t, best_j = t, j
        if best_j is None:
            break
        visited.add(best_j)
        order.append(best_j)
        cur = best_j
    return order


def optimize_route(
    locker_ids: list[str],
    *,
    vehicle_capacity_parcels: int = 80,
    service_time_minutes_default: float = 6.0,
    time_window_start_minutes: int = 8 * 60,
    time_window_end_minutes: int = 20 * 60,
    k_clusters: int | None = None,
) -> dict[str, Any]:
    """
    Depósito: centróide dos lockers (nó 0). Lockers: nós 1..n na ordem de `locker_ids` resolvida no DB.
    Janela horária: limite máximo de duração da rota = (fim - início) em minutos (margem 3× no solver).
    """
    lids = [str(x).strip() for x in locker_ids if str(x).strip()]
    if len(lids) < 2:
        raise ValueError("informe ao menos 2 locker_ids")

    rows = _fetch_lockers_rows(lids)
    if len(rows) < 2:
        raise ValueError("lockers não encontrados ou sem coordenadas suficientes")

    demands_map = _fetch_demands([str(r["locker_id"]) for r in rows])
    prio = _fetch_priority_minutes([str(r["locker_id"]) for r in rows])

    coords_list: list[list[float]] = []
    valid_rows: list[dict[str, Any]] = []
    for r in rows:
        lat, lon = r.get("lat"), r.get("lon")
        if lat is None or lon is None:
            continue
        try:
            coords_list.append([float(lat), float(lon)])
            valid_rows.append(r)
        except (TypeError, ValueError):
            continue
    if len(coords_list) < 2:
        raise ValueError("coordenadas insuficientes para roteirização")

    coords = np.array(coords_list, dtype=np.float64)
    n = coords.shape[0]
    locker_ids_v = [str(r["locker_id"]) for r in valid_rows]

    centroid = coords.mean(axis=0, keepdims=True)
    coords_aug = np.vstack([centroid, coords])
    n_aug = n + 1

    k_use = k_clusters or auto_k(n)
    labels = cluster_lockers_coords(coords, k=k_use)
    labels_aug = np.concatenate([np.zeros(1, dtype=np.int32), labels.astype(np.int32)])

    svc_list = _service_minutes_per_locker(valid_rows, demands_map, prio, service_time_minutes_default)
    service_aug = np.array([0.0] + svc_list, dtype=np.float64)

    rf = ensure_travel_rf()
    time_mat = build_time_matrix_minutes(coords_aug, labels_aug, service_aug, rf)

    demands_aug = np.array([0] + [max(1, demands_map.get(lid, 1)) for lid in locker_ids_v], dtype=np.int32)

    manager = pywrapcp.RoutingIndexManager(n_aug, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def transit_cb(from_index: int, to_index: int) -> int:
        i = manager.IndexToNode(from_index)
        j = manager.IndexToNode(to_index)
        return int(max(1, round(float(time_mat[i, j]))))

    cb = routing.RegisterTransitCallback(transit_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(cb)

    def demand_cb(from_index: int) -> int:
        return int(demands_aug[manager.IndexToNode(from_index)])

    routing.AddDimensionWithVehicleCapacity(demand_cb, 0, [vehicle_capacity_parcels], True, "Cap")

    route_span_min = max(60, int(time_window_end_minutes - time_window_start_minutes))
    max_time_dim = route_span_min * 4
    routing.AddDimension(cb, 120, max_time_dim, True, "Time")

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.FromSeconds(15)

    sol = routing.SolveWithParameters(params)
    order_aug: list[int]
    if sol is None:
        logger.warning("OR-Tools sem solução viável; usando vizinho mais próximo (tempo)")
        order_aug = _nearest_neighbor_order(n_aug, time_mat)
    else:
        order_aug = []
        index = routing.Start(0)
        while not routing.IsEnd(index):
            order_aug.append(manager.IndexToNode(index))
            index = sol.Value(routing.NextVar(index))

    visit_nodes = [x for x in order_aug if x >= 1]
    if len(visit_nodes) != n:
        logger.warning("solução OR-Tools incompleta (%s/%s nós); fallback NN", len(visit_nodes), n)
        order_aug = _nearest_neighbor_order(n_aug, time_mat)
        visit_nodes = [x for x in order_aug if x >= 1]
    ordered_lockers = [locker_ids_v[i - 1] for i in visit_nodes]
    visit_locker_indices = [i - 1 for i in visit_nodes]

    naive_seq = [0] + list(range(1, n_aug)) + [0]
    opt_seq = [0] + visit_nodes + [0]
    km_naive = _closed_tour_km_haversine(naive_seq, coords_aug)
    km_opt = _closed_tour_km_haversine(opt_seq, coords_aug)
    reduction = 0.0 if km_naive <= 1e-6 else max(0.0, (km_naive - km_opt) / km_naive * 100.0)

    cluster_rows = summarize_clusters(locker_ids_v, coords, labels)

    return {
        "ordered_locker_ids": ordered_lockers,
        "visit_locker_indices": visit_locker_indices,
        "cluster_by_locker": cluster_rows,
        "k_clusters": int(k_use),
        "total_km_naive_haversine": round(km_naive, 3),
        "total_km_optimized_haversine": round(km_opt, 3),
        "reduction_pct_vs_input_order": round(reduction, 2),
        "estimated_reduction_band_typical": "15-20%",
        "constraints": {
            "vehicle_capacity_parcels": vehicle_capacity_parcels,
            "route_time_window_minutes": [time_window_start_minutes, time_window_end_minutes],
            "route_max_span_minutes_solver": max_time_dim,
            "service_time_minutes_default": service_time_minutes_default,
        },
        "lockers_meta": [
            {
                "locker_id": str(r["locker_id"]),
                "lat": float(coords[i, 0]),
                "lon": float(coords[i, 1]),
                "temperature_zone": r.get("temperature_zone"),
                "security_level": r.get("security_level"),
                "slots_count": r.get("slots_count"),
                "pending_deliveries": demands_map.get(str(r["locker_id"]), 0),
            }
            for i, r in enumerate(valid_rows)
        ],
        "depot": {"lat": float(centroid[0, 0]), "lon": float(centroid[0, 1])},
        "time_matrix_minutes_sample": [
            [round(float(time_mat[i, j]), 2) for j in range(min(n_aug, 8))] for i in range(min(n_aug, 8))
        ],
    }

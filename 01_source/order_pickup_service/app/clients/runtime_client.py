"""Cliente HTTP tipado para o backend regional de runtime (door_state / slots)."""

from __future__ import annotations

import logging
from typing import Any, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


def _headers(locker_id: Optional[str] = None) -> dict[str, str]:
    h = {"X-Internal-Token": settings.internal_token, "Accept": "application/json"}
    lid = str(locker_id or "").strip().upper()
    if lid:
        h["X-Locker-Id"] = lid
    return h


def _base_url_for_region(region: Optional[str]) -> str:
    r = str(region or "").strip().upper()
    if r:
        return settings.get_runtime_url_for_region(r).rstrip("/")
    return settings.runtime_internal.rstrip("/")


def get_slots(locker_id: str, *, region: Optional[str] = None, timeout_sec: Optional[float] = None) -> list[dict[str, Any]]:
    """
    GET /locker/slots — projeção do door_state local (SQLite) por locker.
    """
    lid = str(locker_id or "").strip().upper()
    if not lid:
        raise ValueError("locker_id is required")
    to = timeout_sec if timeout_sec is not None else float(settings.backend_client_timeout_sec)
    url = f"{_base_url_for_region(region)}/locker/slots"
    resp = requests.get(url, headers=_headers(lid), timeout=to)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise ValueError("runtime /locker/slots: expected JSON array")
    return data


def get_door_state(machine_id: str, *, region: Optional[str] = None, timeout_sec: Optional[float] = None) -> list[dict[str, Any]]:
    """
    O runtime não expõe GET /door_state; usamos a mesma projeção que o painel hardware,
    resolvendo via X-Locker-Id (em muitos deploys machine_id == totem/locker lógico).
    """
    return get_slots(machine_id, region=region, timeout_sec=timeout_sec)


def post_set_state(
    locker_id: str,
    slot: int,
    state: str,
    *,
    region: Optional[str] = None,
    product_id: Optional[str] = None,
    timeout_sec: Optional[float] = None,
) -> dict[str, Any]:
    """POST /locker/slots/{slot}/set-state — corpo canônico do runtime (state + product_id opcional)."""
    lid = str(locker_id or "").strip().upper()
    if not lid:
        raise ValueError("locker_id is required")
    st = str(state or "").strip().upper()
    if not st:
        raise ValueError("state is required")
    to = timeout_sec if timeout_sec is not None else float(settings.backend_client_timeout_sec)
    url = f"{_base_url_for_region(region)}/locker/slots/{int(slot)}/set-state"
    body: dict[str, Any] = {"state": st}
    if product_id is not None:
        body["product_id"] = product_id
    resp = requests.post(
        url,
        headers={**_headers(lid), "Content-Type": "application/json"},
        json=body,
        timeout=to,
    )
    resp.raise_for_status()
    out = resp.json()
    if not isinstance(out, dict):
        raise ValueError("runtime set-state: expected JSON object")
    return out


def send_override(
    locker_id: str,
    slot: int,
    runtime_state: str,
    *,
    region: Optional[str] = None,
    reason: Optional[str] = None,
    timeout_sec: Optional[float] = None,
) -> dict[str, Any]:
    """
    Postgres → runtime: aplica estado no door_state via POST /locker/slots/{slot}/set-state.
    `reason` é apenas para log local (não enviado ao runtime).
    """
    if reason:
        logger.info(
            "runtime send_override locker_id=%s slot=%s state=%s reason=%s",
            locker_id,
            int(slot),
            runtime_state,
            str(reason)[:500],
        )
    return post_set_state(locker_id, int(slot), runtime_state, region=region, timeout_sec=timeout_sec)

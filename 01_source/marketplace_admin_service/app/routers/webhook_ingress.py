"""Recebe POST de webhooks de capacidade (demo / ingress local)."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Request

router = APIRouter(prefix="/webhooks/ingress", tags=["webhook-ingress"])

_last_payloads: list[dict[str, Any]] = []


def pop_last_ingress_payloads() -> list[dict[str, Any]]:
    out = list(_last_payloads)
    _last_payloads.clear()
    return out


@router.post("/{partner_code}/{capability_code}")
async def receive_capability_webhook(
    partner_code: str,
    capability_code: str,
    request: Request,
) -> dict[str, Any]:
    raw = await request.body()
    try:
        body = json.loads(raw.decode("utf-8") if raw else "{}")
    except json.JSONDecodeError:
        body = {"raw": raw.decode("utf-8", errors="replace")[:2000]}
    record = {
        "partner_code": partner_code.upper(),
        "capability_code": capability_code.upper(),
        "event": request.headers.get("X-Ellan-Event"),
        "body": body,
    }
    _last_payloads.append(record)
    if len(_last_payloads) > 200:
        del _last_payloads[:-200]
    return {"ok": True, "received": True, "partner_code": partner_code, "capability_code": capability_code}

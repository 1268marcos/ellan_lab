# 01_source/payment_gateway/app/core/runtime_client.py

from __future__ import annotations

import os
import requests
from typing import Any, Dict


RUNTIME_BASE_URL = os.getenv("LOCKER_RUNTIME_INTERNAL", "").rstrip("/")
INTERNAL_TOKEN = os.getenv("ORDER_INTERNAL_TOKEN", "")

TIMEOUT_SEC = float(os.getenv("BACKEND_CLIENT_TIMEOUT_SEC", "5"))


def _headers(locker_id: str | None = None) -> Dict[str, str]:
    headers = {
        "x-internal-token": INTERNAL_TOKEN,
        "accept": "application/json",
    }
    if locker_id:
        headers["X-Locker-Id"] = locker_id
    return headers


def _request(
    method: str,
    path: str,
    *,
    locker_id: str | None = None,
    json: dict | None = None,
) -> dict:
    url = f"{RUNTIME_BASE_URL}{path}"

    try:
        resp = requests.request(
            method=method,
            url=url,
            headers=_headers(locker_id),
            json=json,
            timeout=TIMEOUT_SEC,
        )
    except requests.RequestException as exc:
        return {
            "ok": False,
            "type": "RUNTIME_CONNECTION_ERROR",
            "message": "Failed to connect to backend_runtime",
            "retryable": True,
            "error": str(exc),
            "url": url,
        }

    if resp.status_code >= 400:
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text}

        return {
            "ok": False,
            "type": "RUNTIME_HTTP_ERROR",
            "status_code": resp.status_code,
            "retryable": resp.status_code >= 500,
            "response": data,
            "url": url,
        }

    try:
        return {
            "ok": True,
            "data": resp.json(),
        }
    except Exception:
        return {
            "ok": False,
            "type": "INVALID_JSON_FROM_RUNTIME",
            "retryable": True,
            "url": url,
        }


# =========================
# LOCKER RESOLUTION
# =========================

def resolve_locker(locker_id: str) -> dict:
    return _request(
        "GET",
        "/internal/runtime/lockers/resolve",
        locker_id=locker_id,
    )


# =========================
# SLOTS / STATE
# =========================

def get_slots(locker_id: str) -> dict:
    return _request(
        "GET",
        "/locker/slots",
        locker_id=locker_id,
    )


def get_slot(locker_id: str, slot: int) -> dict:
    return _request(
        "GET",
        f"/locker/slots/{slot}",
        locker_id=locker_id,
    )


# =========================
# ALLOCATION
# =========================

def allocate_slot(
    locker_id: str,
    *,
    sku_id: str,
) -> dict:
    return _request(
        "POST",
        "/locker/allocate",
        locker_id=locker_id,
        json={
            "sku_id": sku_id,
        },
    )


def commit_allocation(
    locker_id: str,
    allocation_id: str,
) -> dict:
    return _request(
        "POST",
        f"/locker/allocations/{allocation_id}/commit",
        locker_id=locker_id,
    )


def release_allocation(
    locker_id: str,
    allocation_id: str,
) -> dict:
    return _request(
        "POST",
        f"/locker/allocations/{allocation_id}/release",
        locker_id=locker_id,
    )


# =========================
# HARDWARE
# =========================

def open_slot(locker_id: str, slot: int) -> dict:
    return _request(
        "POST",
        f"/locker/slots/{slot}/open",
        locker_id=locker_id,
    )


def light_on(locker_id: str, slot: int) -> dict:
    return _request(
        "POST",
        f"/locker/slots/{slot}/light/on",
        locker_id=locker_id,
    )


# =========================
# CATALOG
# =========================

def get_skus(locker_id: str) -> dict:
    return _request(
        "GET",
        "/catalog/skus",
        locker_id=locker_id,
    )


def get_sku(locker_id: str, sku_id: str) -> dict:
    return _request(
        "GET",
        f"/catalog/skus/{sku_id}",
        locker_id=locker_id,
    )


def get_catalog_slots(locker_id: str) -> dict:
    return _request(
        "GET",
        "/catalog/slots",
        locker_id=locker_id,
    )
# 01_source/backend/order_lifecycle_service/app/clients/runtime_client.py
# 21/04/2026 - cliente mínimo para release operacional no runtime

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


class RuntimeClientError(Exception):
    pass


class RuntimeClient:
    def __init__(self) -> None:
        self.base_url = (
            os.getenv("LOCKER_RUNTIME_INTERNAL")
            or os.getenv("RUNTIME_INTERNAL_URL")
            or "http://backend_runtime:8000"
        ).rstrip("/")

        self.timeout_sec = int(os.getenv("RUNTIME_TIMEOUT_SEC", "8"))
        self.internal_token = (
            os.getenv("INTERNAL_SERVICE_TOKEN")
            or os.getenv("X_INTERNAL_TOKEN")
            or os.getenv("INTERNAL_TOKEN")
            or ""
        ).strip()

    def _headers(self, *, locker_id: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.internal_token:
            headers["X-Internal-Token"] = self.internal_token
        if locker_id:
            headers["X-Locker-Id"] = locker_id
        return headers

    def locker_set_state(
        self,
        *,
        region: str,
        slot: int,
        state: str,
        locker_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/locker/slots/{int(slot)}/set-state"
        payload = {
            "region": region,
            "slot": int(slot),
            "state": state,
        }
        if locker_id:
            payload["totem_id"] = locker_id

        try:
            resp = requests.post(
                url,
                json=payload,
                headers=self._headers(locker_id=locker_id),
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            return resp.json() if resp.content else {"ok": True}
        except Exception as exc:
            raise RuntimeClientError(
                f"locker_set_state failed: slot={slot} state={state} locker_id={locker_id} error={exc}"
            ) from exc

    def locker_release(
        self,
        *,
        region: str,
        allocation_id: str,
        locker_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/locker/allocations/{allocation_id}/release"
        payload = {"region": region}
        if locker_id:
            payload["totem_id"] = locker_id

        try:
            resp = requests.post(
                url,
                json=payload,
                headers=self._headers(locker_id=locker_id),
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            return resp.json() if resp.content else {"ok": True}
        except Exception as exc:
            raise RuntimeClientError(
                f"locker_release failed: allocation_id={allocation_id} locker_id={locker_id} error={exc}"
            ) from exc
        

        
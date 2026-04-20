# 01_source/order_pickup_service/app/core/lifecycle_client.py
# 20/04/2026 - inclusão de def _build_pickup_deadline_key()


from __future__ import annotations

from typing import Any

import requests

from app.core.config import settings


class LifecycleClientError(RuntimeError):
    pass


class LifecycleClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_sec: float | None = None,
        internal_token: str | None = None,
    ) -> None:
        resolved_base_url = base_url or settings.lifecycle_base_url
        self.base_url = str(resolved_base_url or "").rstrip("/")

        resolved_timeout = timeout_sec if timeout_sec is not None else 5
        self.timeout_sec = float(resolved_timeout)

        resolved_token = internal_token or settings.internal_token
        self.internal_token = str(resolved_token or "").strip()

        if not self.base_url:
            raise LifecycleClientError("ORDER_LIFECYCLE_BASE_URL não configurado.")

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }

        if self.internal_token:
            headers["X-Internal-Token"] = self.internal_token

        return headers

    def _request(
        self,
        *,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._headers(),
                json=json_body,
                timeout=self.timeout_sec,
            )
        except requests.RequestException as exc:
            raise LifecycleClientError(
                f"Falha de comunicação com order_lifecycle_service: {exc}"
            ) from exc

        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text

            raise LifecycleClientError(
                f"order_lifecycle_service retornou erro HTTP {response.status_code}: {detail}"
            )

        if not response.content:
            return {}

        try:
            return response.json()
        except Exception as exc:
            raise LifecycleClientError(
                "Resposta inválida do order_lifecycle_service: JSON malformado."
            ) from exc

    @staticmethod
    def _build_prepayment_deadline_key(order_id: str) -> str:
        return f"order:{order_id}:prepayment_timeout"

    def create_prepayment_deadline(
        self,
        *,
        order_id: str,
        order_channel: str,
        region_code: str | None,
        slot_id: str | None,
        machine_id: str | None,
        deadline_at: str | None,
        payment_method: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "deadline_key": self._build_prepayment_deadline_key(order_id),
            "order_id": order_id,
            "order_channel": order_channel,
            "deadline_type": "PREPAYMENT_TIMEOUT",
            "due_at": deadline_at,
            "payload": {
                "region_code": region_code,
                "slot_id": slot_id,
                "machine_id": machine_id,
                "payment_method": payment_method,
            },
        }

        return self._request(
            method="POST",
            path="/internal/deadlines",
            json_body=payload,
        )



    # 20/04/2026
    @staticmethod
    def _build_pickup_deadline_key(order_id: str) -> str:
        return f"order:{order_id}:pickup_deadline"

    def create_pickup_deadline(
        self,
        *,
        order_id: str,
        order_channel: str,
        region_code: str | None,
        slot_id: str | None,
        machine_id: str | None,
        deadline_at: str | None,
        payment_method: str | None = None,
        reminder_schedule: list[str] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "deadline_key": self._build_pickup_deadline_key(order_id),
            "order_id": order_id,
            "order_channel": order_channel,
            "deadline_type": "PICKUP_TIMEOUT",
            "due_at": deadline_at,
            "payload": {
                "region_code": region_code,
                "slot_id": slot_id,
                "machine_id": machine_id,
                "payment_method": payment_method,
                "reminder_schedule": reminder_schedule or [],
            },
        }

        return self._request(
            method="POST",
            path="/internal/deadlines",
            json_body=payload,
        )




    def cancel_prepayment_deadline(
        self,
        *,
        order_id: str,
    ) -> dict[str, Any]:
        payload = {
            "deadline_key": self._build_prepayment_deadline_key(order_id),
        }

        return self._request(
            method="POST",
            path="/internal/deadlines/cancel",
            json_body=payload,
        )
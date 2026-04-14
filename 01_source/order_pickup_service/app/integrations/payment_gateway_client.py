# 01_source/order_pickup_service/app/integrations/payment_gateway_client.py
# 13/04/2026

from __future__ import annotations

from typing import Any, Dict, Iterable
import requests

from app.core.config import settings


class PaymentGatewayClientError(Exception):
    pass


class PaymentGatewayClient:
    def __init__(self) -> None:
        self.base_url = (
            getattr(settings, "payment_gateway_url", None)
            or getattr(settings, "payment_gateway_service_url", None)
            or "http://payment_gateway:8000"
        ).rstrip("/")

        self.timeout_sec = int(
            getattr(settings, "payment_gateway_timeout_sec", 10)
            or 10
        )

        self.internal_token = getattr(settings, "internal_token", None)

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.internal_token:
            headers["X-Internal-Token"] = self.internal_token
        return headers

    def _candidate_paths(self) -> Iterable[str]:
        return (
            "/gateway/payment/create",
            "/gateway/payments/create",
            "/payments/create",
            "/payments",
            "/gateway/payment",
        )

    def create_payment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {
            "order_id": payload["order_id"],
            "amount": payload["amount"],
            "currency": payload.get("currency", "BRL"),
            "country": payload.get("country", "BR"),

            # compat
            "method": payload.get("method"),
            "payment_method": payload.get("payment_method") or payload.get("method"),
            
            # "region": payload.get("region"),
            # "locker_id": payload.get("locker_id"),
            # "slot": payload.get("slot"),
            # gateway espera estes nomes
            "regiao": payload.get("region"),
            "porta": payload.get("slot"),
            "locker_id": payload.get("locker_id"),

            "customer_reference": payload.get("customer_reference"),
            "metadata": payload.get("metadata", {}),
        }

        last_error: str | None = None

        for path in self._candidate_paths():
            url = f"{self.base_url}{path}"
            try:
                response = requests.post(
                    url,
                    json=normalized,
                    headers=self._headers(),
                    timeout=self.timeout_sec,
                )
            except requests.RequestException as exc:
                last_error = f"{url} -> {exc}"
                continue

            if response.status_code >= 400:
                try:
                    detail = response.json()
                except Exception:
                    detail = response.text
                last_error = f"{url} -> status={response.status_code} detail={detail}"
                continue

            try:
                data = response.json()
            except Exception as exc:
                raise PaymentGatewayClientError(
                    f"Resposta inválida do payment_gateway em {url}: {exc}"
                ) from exc

            return {
                "provider": data.get("provider"),
                "provider_payment_id": data.get("provider_payment_id") or data.get("payment_id") or data.get("id"),
                "status": data.get("status"),
                "raw_status": data.get("raw_status") or data.get("status"),
                "redirect_url": data.get("redirect_url"),
                "qr_code": data.get("qr_code"),
                "qr_code_text": data.get("qr_code_text") or data.get("pix_code"),
                "authorization_code": data.get("authorization_code"),
                "raw": data,
            }

        raise PaymentGatewayClientError(
            f"Falha ao criar pagamento no payment_gateway. Último erro: {last_error}"
        )
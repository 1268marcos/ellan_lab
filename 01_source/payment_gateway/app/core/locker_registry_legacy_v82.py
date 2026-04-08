# 01_source/payment_gateway/app/core/locker_registry.py
# 07/04/2026 - eliminado o registry legado como fonte principal e alinhando o gateway 100% ao runtime

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from app.core.config import settings


VALID_REGIONS = {"SP", "PT"}
VALID_CHANNELS = {"ONLINE", "KIOSK"}

# Métodos canônicos internos do gateway
CANONICAL_PAYMENT_METHODS = {
    "PIX",
    "CARTAO",
    "MBWAY",
    "MULTIBANCO_REFERENCE",
    "NFC",
    "APPLE_PAY",
    "GOOGLE_PAY",
    "MERCADO_PAGO_WALLET",
}


class LockerRegistryError(ValueError):
    """Erro base do registry de lockers."""


class LockerNotFoundError(LockerRegistryError):
    """Locker não encontrado no registry."""


class LockerInactiveError(LockerRegistryError):
    """Locker encontrado, porém inativo."""


class LockerRegionMismatchError(LockerRegistryError):
    """Locker pertence a outra região."""


class LockerChannelNotAllowedError(LockerRegistryError):
    """Canal não permitido para o locker."""


class LockerPaymentMethodNotAllowedError(LockerRegistryError):
    """Método de pagamento não permitido para o locker."""


def _nullable_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_upper_str(value: Any) -> str:
    return str(value or "").strip().upper()


def _dedupe_preserve_order(values: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _canonical_payment_method(value: Any) -> str:
    raw = _normalize_upper_str(value)
    if not raw:
        return ""

    method_map = {
        # cartões -> CARTAO
        "CARTAO": "CARTAO",
        "CREDITCARD": "CARTAO",
        "DEBITCARD": "CARTAO",
        "GIFTCARD": "CARTAO",
        "PREPAIDCARD": "CARTAO",
        "CREDIT_CARD": "CARTAO",
        "DEBIT_CARD": "CARTAO",
        "GIFT_CARD": "CARTAO",
        "PREPAID_CARD": "CARTAO",
        "CARTAO_CREDITO": "CARTAO",
        "CARTAO_DEBITO": "CARTAO",
        "CARTAO_PRESENTE": "CARTAO",
        "CARTÃO_CREDITO": "CARTAO",
        "CARTÃO_DEBITO": "CARTAO",
        "CARTÃO_PRESENTE": "CARTAO",

        # pix
        "PIX": "PIX",

        # pt/eu
        "MBWAY": "MBWAY",
        "MULTIBANCO_REFERENCE": "MULTIBANCO_REFERENCE",
        "MULTIBANCO": "MULTIBANCO_REFERENCE",

        # wallets / integrações planejadas
        "NFC": "NFC",
        "APPLE_PAY": "APPLE_PAY",
        "GOOGLE_PAY": "GOOGLE_PAY",
        "MERCADO_PAGO_WALLET": "MERCADO_PAGO_WALLET",
        "MERCADO_PAGO": "MERCADO_PAGO_WALLET",
    }

    return method_map.get(raw, raw)


@dataclass(frozen=True)
class LockerAddress:
    address: Optional[str]
    number: Optional[str]
    additional_information: Optional[str]
    locality: Optional[str]
    city: Optional[str]
    federative_unit: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]

    @classmethod
    def from_runtime_item(cls, item: Dict[str, Any]) -> "LockerAddress":
        address = item.get("address")

        if isinstance(address, dict):
            return cls(
                address=_nullable_str(address.get("address")),
                number=_nullable_str(address.get("number")),
                additional_information=_nullable_str(address.get("additional_information")),
                locality=_nullable_str(address.get("locality")),
                city=_nullable_str(address.get("city")),
                federative_unit=_nullable_str(address.get("federative_unit")),
                postal_code=_nullable_str(address.get("postal_code")),
                country=_nullable_str(address.get("country")),
            )

        return cls(
            address=_nullable_str(item.get("address")),
            number=_nullable_str(item.get("number")),
            additional_information=_nullable_str(item.get("additional_information")),
            locality=_nullable_str(item.get("locality")),
            city=_nullable_str(item.get("city")),
            federative_unit=_nullable_str(item.get("state") or item.get("federative_unit")),
            postal_code=_nullable_str(item.get("postal_code")),
            country=_nullable_str(item.get("country")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "number": self.number,
            "additional_information": self.additional_information,
            "locality": self.locality,
            "city": self.city,
            "federative_unit": self.federative_unit,
            "postal_code": self.postal_code,
            "country": self.country,
        }


@dataclass(frozen=True)
class LockerConfig:
    locker_id: str
    region: str
    site_id: Optional[str]
    display_name: str
    backend_region: str
    slots: int
    channels: List[str]
    payment_methods: List[str]  # armazenados em formato canônico interno
    active: bool
    address: LockerAddress

    @classmethod
    def from_runtime_item(cls, item: Dict[str, Any]) -> "LockerConfig":
        locker_id = str(
            item.get("locker_id")
            or item.get("id")
            or item.get("machine_id")
            or ""
        ).strip().upper()

        if not locker_id:
            raise LockerRegistryError("Locker do runtime sem locker_id.")

        region = _normalize_upper_str(item.get("region"))
        if region not in VALID_REGIONS:
            raise LockerRegistryError(
                f"Locker {locker_id}: region inválida no runtime: {region!r}"
            )

        backend_region = _normalize_upper_str(item.get("backend_region") or item.get("region"))
        if backend_region not in VALID_REGIONS:
            backend_region = region

        display_name = str(item.get("display_name") or locker_id).strip()
        site_id = _nullable_str(item.get("site_id"))

        slots_raw = (
            item.get("slot_count_total")
            or item.get("slots_count")
            or item.get("slots")
            or 0
        )
        try:
            slots = int(slots_raw)
        except Exception as exc:
            raise LockerRegistryError(
                f"Locker {locker_id}: campo slots inválido: {slots_raw!r}"
            ) from exc

        if slots < 1:
            raise LockerRegistryError(
                f"Locker {locker_id}: campo slots deve ser maior que zero."
            )

        channels_raw = item.get("allowed_channels") or item.get("channels") or ["ONLINE", "KIOSK"]
        channels = [_normalize_upper_str(v) for v in channels_raw]
        channels = _dedupe_preserve_order(channels)

        if not channels:
            raise LockerRegistryError(
                f"Locker {locker_id}: lista channels vazia."
            )

        invalid_channels = [c for c in channels if c not in VALID_CHANNELS]
        if invalid_channels:
            raise LockerRegistryError(
                f"Locker {locker_id}: channels inválidos: {invalid_channels!r}"
            )

        methods_raw = (
            item.get("payment_methods")
            or item.get("allowed_payment_methods")
            or []
        )
        payment_methods = [_canonical_payment_method(v) for v in methods_raw]
        payment_methods = _dedupe_preserve_order([m for m in payment_methods if m])

        if not payment_methods:
            raise LockerRegistryError(
                f"Locker {locker_id}: lista payment_methods vazia."
            )

        invalid_methods = [m for m in payment_methods if m not in CANONICAL_PAYMENT_METHODS]
        if invalid_methods:
            raise LockerRegistryError(
                f"Locker {locker_id}: payment_methods inválidos após normalização: {invalid_methods!r}"
            )

        return cls(
            locker_id=locker_id,
            region=region,
            site_id=site_id,
            display_name=display_name,
            backend_region=backend_region,
            slots=slots,
            channels=channels,
            payment_methods=payment_methods,
            active=bool(item.get("active", False)),
            address=LockerAddress.from_runtime_item(item),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "locker_id": self.locker_id,
            "region": self.region,
            "site_id": self.site_id,
            "display_name": self.display_name,
            "backend_region": self.backend_region,
            "slots": self.slots,
            "channels": list(self.channels),
            "payment_methods": list(self.payment_methods),
            "active": self.active,
            "address": self.address.to_dict(),
        }


class LockerRegistry:
    """
    Registry canônico de lockers do gateway.

    Fonte única:
    - backend_runtime /internal/runtime/lockers

    Responsabilidades:
    - carregar lockers do runtime
    - resolver fallback legado apenas para ausência de locker_id
    - validar compatibilidade entre locker, região, canal e método de pagamento
    """

    def __init__(self) -> None:
        self._lockers: Dict[str, LockerConfig] = {}

    def _runtime_url(self) -> str:
        return f"{settings.RUNTIME_BASE_URL.rstrip('/')}/internal/runtime/lockers"

    def _runtime_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        token = (settings.INTERNAL_SERVICE_TOKEN or "").strip()
        if token:
            headers["X-Internal-Token"] = token
        return headers

    def _extract_items(self, payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            return [item for item in payload["items"] if isinstance(item, dict)]
        return []

    def _load_registry(self) -> Dict[str, LockerConfig]:
        url = self._runtime_url()

        try:
            response = requests.get(
                url,
                headers=self._runtime_headers(),
                timeout=getattr(settings, "CONNECTION_TIMEOUT_SEC", 10),
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            raise LockerRegistryError(
                f"Falha ao consultar runtime para carregar lockers: {exc}"
            ) from exc
        except ValueError as exc:
            raise LockerRegistryError(
                f"Resposta inválida do runtime ao carregar lockers: {exc}"
            ) from exc

        items = self._extract_items(payload)
        parsed: Dict[str, LockerConfig] = {}

        for item in items:
            cfg = LockerConfig.from_runtime_item(item)
            parsed[cfg.locker_id] = cfg

        return parsed

    def _ensure_loaded(self) -> None:
        if not self._lockers:
            self._lockers = self._load_registry()

    def refresh(self) -> None:
        self._lockers = self._load_registry()

    def all(self) -> Dict[str, LockerConfig]:
        self._ensure_loaded()
        return dict(self._lockers)

    def all_public_summaries(self) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        return [cfg.to_dict() for cfg in self._lockers.values()]

    def list_by_region(self, region: str) -> Dict[str, LockerConfig]:
        self._ensure_loaded()
        region_u = _normalize_upper_str(region)
        return {
            locker_id: cfg
            for locker_id, cfg in self._lockers.items()
            if cfg.region == region_u
        }

    def list_public_summaries_by_region(self, region: str) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        region_u = _normalize_upper_str(region)
        return [
            cfg.to_dict()
            for cfg in self._lockers.values()
            if cfg.region == region_u
        ]

    def get(self, locker_id: str) -> LockerConfig:
        self._ensure_loaded()
        normalized = str(locker_id or "").strip().upper()
        cfg = self._lockers.get(normalized)
        if not cfg:
            raise LockerNotFoundError(f"Locker não encontrado: {locker_id!r}")
        return cfg

    def exists(self, locker_id: str) -> bool:
        self._ensure_loaded()
        normalized = str(locker_id or "").strip().upper()
        return normalized in self._lockers

    def resolve_locker_id(
        self,
        *,
        locker_id: Optional[str],
        region: Optional[str],
        allow_legacy_fallback: bool = True,
    ) -> str:
        self._ensure_loaded()

        explicit = str(locker_id or "").strip().upper()
        if explicit:
            return explicit

        if not allow_legacy_fallback:
            raise LockerNotFoundError("locker_id é obrigatório e não foi informado.")

        region_u = _normalize_upper_str(region)
        if not region_u:
            raise LockerNotFoundError(
                "locker_id ausente e região não informada para fallback legado."
            )

        legacy = settings.get_legacy_locker_id(region_u)
        if legacy:
            return str(legacy).strip().upper()

        default_locker = settings.DEFAULT_LOCKER_ID
        if default_locker:
            return str(default_locker).strip().upper()

        raise LockerNotFoundError(
            f"locker_id ausente e nenhum fallback legado configurado para a região {region_u}."
        )

    def ensure_active(self, locker_id: str) -> LockerConfig:
        cfg = self.get(locker_id)
        if not cfg.active:
            raise LockerInactiveError(f"Locker inativo: {locker_id}")
        return cfg

    def ensure_region(self, locker_id: str, region: str) -> LockerConfig:
        cfg = self.get(locker_id)
        region_u = _normalize_upper_str(region)

        if cfg.region != region_u:
            raise LockerRegionMismatchError(
                f"Locker {locker_id} pertence à região {cfg.region}, não à região {region_u}."
            )
        return cfg

    def ensure_channel_allowed(self, locker_id: str, channel: str) -> LockerConfig:
        cfg = self.get(locker_id)
        channel_u = _normalize_upper_str(channel)

        if channel_u not in cfg.channels:
            raise LockerChannelNotAllowedError(
                f"Canal {channel_u} não permitido para o locker {locker_id}."
            )
        return cfg

    def ensure_payment_method_allowed(self, locker_id: str, payment_method: str) -> LockerConfig:
        cfg = self.get(locker_id)
        payment_method_u = _canonical_payment_method(payment_method)

        if payment_method_u not in cfg.payment_methods:
            raise LockerPaymentMethodNotAllowedError(
                f"Método {payment_method_u} não permitido para o locker {locker_id}."
            )
        return cfg

    def validate_context(
        self,
        *,
        locker_id: str,
        region: str,
        channel: str,
        payment_method: str,
        require_active: bool = True,
    ) -> LockerConfig:
        cfg = self.get(locker_id)

        if require_active and not cfg.active:
            raise LockerInactiveError(f"Locker inativo: {locker_id}")

        region_u = _normalize_upper_str(region)
        channel_u = _normalize_upper_str(channel)
        payment_method_u = _canonical_payment_method(payment_method)

        if cfg.region != region_u:
            raise LockerRegionMismatchError(
                f"Locker {locker_id} pertence à região {cfg.region}, não à região {region_u}."
            )

        if channel_u not in cfg.channels:
            raise LockerChannelNotAllowedError(
                f"Canal {channel_u} não permitido para o locker {locker_id}."
            )

        if payment_method_u not in cfg.payment_methods:
            raise LockerPaymentMethodNotAllowedError(
                f"Método {payment_method_u} não permitido para o locker {locker_id}."
            )

        return cfg

    def get_backend_region(self, locker_id: str) -> str:
        cfg = self.get(locker_id)
        return cfg.backend_region

    def get_backend_url(self, locker_id: str) -> str:
        backend_region = self.get_backend_region(locker_id)
        return settings.get_regional_url(backend_region)

    def get_address_dict(self, locker_id: str) -> Dict[str, Any]:
        cfg = self.get(locker_id)
        return cfg.address.to_dict()

    def get_public_summary(self, locker_id: str) -> Dict[str, Any]:
        cfg = self.get(locker_id)
        return cfg.to_dict()


locker_registry = LockerRegistry()



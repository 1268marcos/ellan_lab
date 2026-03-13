from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.core.config import settings


VALID_REGIONS = {"SP", "PT"}
VALID_CHANNELS = {"ONLINE", "KIOSK"}
VALID_PAYMENT_METHODS = {
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


@dataclass(frozen=True)
class LockerAddress:
    address: str
    number: Optional[str]
    additional_information: Optional[str]
    locality: Optional[str]
    city: Optional[str]
    federative_unit: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LockerAddress":
        return cls(
            address=str(data.get("address") or "").strip(),
            number=str(data.get("number")).strip() if data.get("number") is not None else None,
            additional_information=_nullable_str(data.get("additional_information")),
            locality=_nullable_str(data.get("locality")),
            city=_nullable_str(data.get("city")),
            federative_unit=_nullable_str(data.get("federative_unit")),
            postal_code=_nullable_str(data.get("postal_code")),
            country=_nullable_str(data.get("country")),
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
    site_id: str
    display_name: str
    backend_region: str
    slots: int
    channels: List[str]
    payment_methods: List[str]
    active: bool
    address: LockerAddress

    @classmethod
    def from_dict(cls, locker_id: str, data: Dict[str, Any]) -> "LockerConfig":
        region = _upper_required(data, "region", locker_id)
        if region not in VALID_REGIONS:
            raise LockerRegistryError(
                f"Locker {locker_id}: region inválida: {region!r}."
            )

        backend_region = str(data.get("backend_region") or region).strip().upper()
        if backend_region not in VALID_REGIONS:
            raise LockerRegistryError(
                f"Locker {locker_id}: backend_region inválida: {backend_region!r}."
            )

        site_id = _required_str(data, "site_id", locker_id)
        display_name = _required_str(data, "display_name", locker_id)

        slots_raw = data.get("slots", 24)
        try:
            slots = int(slots_raw)
        except Exception as exc:
            raise LockerRegistryError(
                f"Locker {locker_id}: campo 'slots' inválido: {slots_raw!r}"
            ) from exc

        if slots < 1:
            raise LockerRegistryError(
                f"Locker {locker_id}: campo 'slots' deve ser maior que zero."
            )

        channels = [_normalize_upper_str(v) for v in (data.get("channels") or [])]
        channels = _dedupe_preserve_order(channels)

        payment_methods = [_normalize_upper_str(v) for v in (data.get("payment_methods") or [])]
        payment_methods = _dedupe_preserve_order(payment_methods)

        if not channels:
            raise LockerRegistryError(
                f"Locker {locker_id}: lista 'channels' não pode estar vazia."
            )

        invalid_channels = [c for c in channels if c not in VALID_CHANNELS]
        if invalid_channels:
            raise LockerRegistryError(
                f"Locker {locker_id}: channels inválidos: {invalid_channels!r}"
            )

        if not payment_methods:
            raise LockerRegistryError(
                f"Locker {locker_id}: lista 'payment_methods' não pode estar vazia."
            )

        invalid_methods = [m for m in payment_methods if m not in VALID_PAYMENT_METHODS]
        if invalid_methods:
            raise LockerRegistryError(
                f"Locker {locker_id}: payment_methods inválidos: {invalid_methods!r}"
            )

        address = LockerAddress.from_dict(data)

        if not address.address:
            raise LockerRegistryError(
                f"Locker {locker_id}: campo 'address' é obrigatório."
            )

        return cls(
            locker_id=locker_id.strip(),
            region=region,
            site_id=site_id,
            display_name=display_name,
            backend_region=backend_region,
            slots=slots,
            channels=channels,
            payment_methods=payment_methods,
            active=bool(data.get("active", False)),
            address=address,
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


def _nullable_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_upper_str(value: Any) -> str:
    return str(value or "").strip().upper()


def _required_str(data: Dict[str, Any], key: str, locker_id: str) -> str:
    value = str(data.get(key) or "").strip()
    if not value:
        raise LockerRegistryError(f"Locker {locker_id}: campo '{key}' é obrigatório.")
    return value


def _upper_required(data: Dict[str, Any], key: str, locker_id: str) -> str:
    return _required_str(data, key, locker_id).upper()


def _dedupe_preserve_order(values: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


class LockerRegistry:
    """
    Registry de lockers do gateway.

    Responsabilidades:
    - carregar e validar configurações de lockers
    - resolver fallback legado por região, se necessário
    - validar compatibilidade entre locker, região, canal e método de pagamento
    """

    def __init__(self) -> None:
        self._lockers: Dict[str, LockerConfig] = self._load_registry()

    def _load_registry(self) -> Dict[str, LockerConfig]:
        raw_registry = settings.locker_registry
        parsed: Dict[str, LockerConfig] = {}

        for locker_id, payload in raw_registry.items():
            normalized_locker_id = str(locker_id or "").strip()
            if not normalized_locker_id:
                raise LockerRegistryError("LOCKER_REGISTRY_JSON contém locker_id vazio.")

            if not isinstance(payload, dict):
                raise LockerRegistryError(
                    f"Locker {normalized_locker_id}: configuração deve ser um objeto."
                )

            parsed[normalized_locker_id] = LockerConfig.from_dict(
                normalized_locker_id,
                payload,
            )

        return parsed

    def all(self) -> Dict[str, LockerConfig]:
        return dict(self._lockers)

    def all_public_summaries(self) -> List[Dict[str, Any]]:
        return [cfg.to_dict() for cfg in self._lockers.values()]

    def list_by_region(self, region: str) -> Dict[str, LockerConfig]:
        region_u = _normalize_upper_str(region)
        return {
            locker_id: cfg
            for locker_id, cfg in self._lockers.items()
            if cfg.region == region_u
        }

    def list_public_summaries_by_region(self, region: str) -> List[Dict[str, Any]]:
        region_u = _normalize_upper_str(region)
        return [
            cfg.to_dict()
            for cfg in self._lockers.values()
            if cfg.region == region_u
        ]

    def get(self, locker_id: str) -> LockerConfig:
        normalized = str(locker_id or "").strip()
        cfg = self._lockers.get(normalized)
        if not cfg:
            raise LockerNotFoundError(f"Locker não encontrado: {locker_id!r}")
        return cfg

    def exists(self, locker_id: str) -> bool:
        normalized = str(locker_id or "").strip()
        return normalized in self._lockers

    def resolve_locker_id(
        self,
        *,
        locker_id: Optional[str],
        region: Optional[str],
        allow_legacy_fallback: bool = True,
    ) -> str:
        explicit = str(locker_id or "").strip()
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
            return legacy

        default_locker = settings.DEFAULT_LOCKER_ID
        if default_locker:
            return default_locker

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
        payment_method_u = _normalize_upper_str(payment_method)

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
        payment_method_u = _normalize_upper_str(payment_method)

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
        return {
            "locker_id": cfg.locker_id,
            "region": cfg.region,
            "site_id": cfg.site_id,
            "display_name": cfg.display_name,
            "backend_region": cfg.backend_region,
            "slots": cfg.slots,
            "channels": list(cfg.channels),
            "payment_methods": list(cfg.payment_methods),
            "active": cfg.active,
            "address": cfg.address.to_dict(),
        }


locker_registry = LockerRegistry()
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import settings


@dataclass
class FeatureFlagSnapshot:
    use_catalog_service: bool
    use_partner_service: bool
    use_inventory_service: bool
    use_wallet_service: bool
    shadow_mode_enabled: bool
    auto_rollback_enabled: bool


_runtime_overrides: dict[str, bool] = {}


def set_flag_override(name: str, value: bool | None) -> None:
    if value is None:
        _runtime_overrides.pop(name, None)
    else:
        _runtime_overrides[name] = value


def _get_bool(name: str, default: bool) -> bool:
    if name in _runtime_overrides:
        return bool(_runtime_overrides[name])
    return default


def use_catalog_service() -> bool:
    return _get_bool("USE_CATALOG_SERVICE", bool(settings.use_catalog_service))


def use_partner_service() -> bool:
    return _get_bool("USE_PARTNER_SERVICE", bool(settings.use_partner_service))


def use_inventory_service() -> bool:
    return _get_bool("USE_INVENTORY_SERVICE", bool(settings.use_inventory_service))


def use_wallet_service() -> bool:
    return _get_bool("USE_WALLET_SERVICE", bool(settings.use_wallet_service))


def shadow_mode_enabled() -> bool:
    return _get_bool("SHADOW_MODE_ENABLED", bool(settings.shadow_mode_enabled))


def auto_rollback_enabled() -> bool:
    return _get_bool("AUTO_ROLLBACK_ENABLED", bool(settings.auto_rollback_enabled))


def snapshot() -> FeatureFlagSnapshot:
    return FeatureFlagSnapshot(
        use_catalog_service=use_catalog_service(),
        use_partner_service=use_partner_service(),
        use_inventory_service=use_inventory_service(),
        use_wallet_service=use_wallet_service(),
        shadow_mode_enabled=shadow_mode_enabled(),
        auto_rollback_enabled=auto_rollback_enabled(),
    )


def as_public_dict() -> dict[str, Any]:
    s = snapshot()
    return {
        "USE_CATALOG_SERVICE": s.use_catalog_service,
        "USE_PARTNER_SERVICE": s.use_partner_service,
        "USE_INVENTORY_SERVICE": s.use_inventory_service,
        "USE_WALLET_SERVICE": s.use_wallet_service,
        "SHADOW_MODE_ENABLED": s.shadow_mode_enabled,
        "AUTO_ROLLBACK_ENABLED": s.auto_rollback_enabled,
    }


def apply_rollback_all_off() -> None:
    for k in (
        "USE_CATALOG_SERVICE",
        "USE_PARTNER_SERVICE",
        "USE_INVENTORY_SERVICE",
        "USE_WALLET_SERVICE",
        "SHADOW_MODE_ENABLED",
    ):
        _runtime_overrides[k] = False


@dataclass
class FlagMetrics:
    total_requests: int = 0
    error_responses: int = 0
    last_error_rate: float = 0.0


_metrics = FlagMetrics()


def record_http_outcome(*, status_code: int) -> None:
    _metrics.total_requests += 1
    if int(status_code) >= 400:
        _metrics.error_responses += 1
    if _metrics.total_requests:
        _metrics.last_error_rate = _metrics.error_responses / _metrics.total_requests


def get_metrics() -> dict[str, Any]:
    return {
        "total_requests": _metrics.total_requests,
        "error_responses": _metrics.error_responses,
        "last_error_rate": round(_metrics.last_error_rate, 6),
    }


def reset_metrics() -> None:
    _metrics.total_requests = 0
    _metrics.error_responses = 0
    _metrics.last_error_rate = 0.0


def reset_overrides() -> None:
    _runtime_overrides.clear()

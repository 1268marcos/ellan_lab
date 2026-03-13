# 01_source/payment_gateway/app/core/config.py
import json
import os
from functools import cached_property
from typing import Any, Dict, Optional


class Settings:
    # ------------------------------------------------------------------
    # Backends regionais
    # ------------------------------------------------------------------
    BACKEND_SP: str = os.getenv("BACKEND_SP", "http://backend_sp:8000")
    BACKEND_PT: str = os.getenv("BACKEND_PT", "http://backend_pt:8000")

    BACKEND_SP_PATH: str = os.getenv("BACKEND_SP_PATH", "")
    BACKEND_PT_PATH: str = os.getenv("BACKEND_PT_PATH", "")

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis_central")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

    # ------------------------------------------------------------------
    # MQTT
    # ------------------------------------------------------------------
    MQTT_HOST: str = os.getenv("MQTT_HOST", "mqtt_broker")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))

    # ------------------------------------------------------------------
    # SQLite
    # ------------------------------------------------------------------
    SQLITE_PATH: str = os.getenv("GATEWAY_SQLITE_PATH", "/data/sqlite/gateway/events.db")

    # ------------------------------------------------------------------
    # Anti-fraude / auditoria
    # ------------------------------------------------------------------
    ANTIFRAUD_ACTIVE_PEPPER_VERSION: str = os.getenv("ANTIFRAUD_ACTIVE_PEPPER_VERSION", "v1")
    ANTIFRAUD_PEPPER_V1: Optional[str] = os.getenv("ANTIFRAUD_PEPPER_V1")
    ANTIFRAUD_PEPPER_V2: Optional[str] = os.getenv("ANTIFRAUD_PEPPER_V2")
    LOG_HASH_SALT: Optional[str] = os.getenv("LOG_HASH_SALT")

    # ------------------------------------------------------------------
    # Idempotência
    # ------------------------------------------------------------------
    IDEMPOTENCY_TTL_SEC: int = int(os.getenv("IDEMPOTENCY_TTL_SEC", "86400"))

    # ------------------------------------------------------------------
    # Device fingerprint
    # ------------------------------------------------------------------
    DEVICE_FP_VERSION: str = os.getenv("DEVICE_FP_VERSION", "v1_web")

    # ------------------------------------------------------------------
    # Gateway
    # ------------------------------------------------------------------
    GATEWAY_ID: str = os.getenv("GATEWAY_ID", "payment_gateway_01")
    GATEWAY_LOG_DIR: str = os.getenv("GATEWAY_LOG_DIR", "/logs")

    # ------------------------------------------------------------------
    # Compatibilidade legada
    # ------------------------------------------------------------------
    DEFAULT_LOCKER_ID: Optional[str] = (
        os.getenv("DEFAULT_LOCKER_ID")
        or os.getenv("MACHINE_ID")
        or os.getenv("LOCKER_ID")
    )

    LEGACY_LOCKER_ID_SP: Optional[str] = (
        os.getenv("LOCKER_ID_SP")
        or os.getenv("MACHINE_ID_SP")
    )

    LEGACY_LOCKER_ID_PT: Optional[str] = (
        os.getenv("LOCKER_ID_PT")
        or os.getenv("MACHINE_ID_PT")
    )

    # ------------------------------------------------------------------
    # Multi-locker registry
    # ------------------------------------------------------------------
    LOCKER_REGISTRY_JSON: str = os.getenv("LOCKER_REGISTRY_JSON", "").strip()

    @property
    def REGIONAL_BACKENDS(self) -> Dict[str, str]:
        return {
            "SP": self.BACKEND_SP,
            "PT": self.BACKEND_PT,
        }

    @property
    def REGIONAL_PATHS(self) -> Dict[str, str]:
        return {
            "SP": self.BACKEND_SP_PATH,
            "PT": self.BACKEND_PT_PATH,
        }

    def get_regional_url(self, region: str) -> str:
        reg = (region or "").upper().strip()
        if reg == "SP":
            return self.BACKEND_SP.rstrip("/")
        if reg == "PT":
            return self.BACKEND_PT.rstrip("/")
        raise ValueError(f"Unknown region: {region}")

    def get_legacy_locker_id(self, region: str) -> Optional[str]:
        reg = (region or "").upper().strip()
        if reg == "SP":
            return self.LEGACY_LOCKER_ID_SP
        if reg == "PT":
            return self.LEGACY_LOCKER_ID_PT
        return None

    @cached_property
    def locker_registry(self) -> Dict[str, Dict[str, Any]]:
        """
        Carrega o registry de lockers a partir de LOCKER_REGISTRY_JSON.
        Deve ser um objeto JSON com locker_id -> config.
        """
        raw = self.LOCKER_REGISTRY_JSON
        if not raw:
            return {}

        try:
            parsed = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(f"LOCKER_REGISTRY_JSON inválido: {exc}") from exc

        if not isinstance(parsed, dict):
            raise RuntimeError("LOCKER_REGISTRY_JSON deve ser um objeto JSON.")

        normalized: Dict[str, Dict[str, Any]] = {}
        for locker_id, cfg in parsed.items():
            key = str(locker_id or "").strip().upper()
            if not key:
                raise RuntimeError("LOCKER_REGISTRY_JSON contém locker_id vazio.")
            if not isinstance(cfg, dict):
                raise RuntimeError(f"Configuração do locker {key} deve ser um objeto JSON.")
            normalized[key] = cfg

        return normalized

    def get_locker_config(self, locker_id: str) -> Optional[Dict[str, Any]]:
        normalized = str(locker_id or "").strip().upper()
        if not normalized:
            return None
        return self.locker_registry.get(normalized)

    def get_locker_region(self, locker_id: str) -> Optional[str]:
        cfg = self.get_locker_config(locker_id)
        if not cfg:
            return None
        return (cfg.get("region") or "").strip().upper() or None

    def get_locker_backend_region(self, locker_id: str) -> Optional[str]:
        cfg = self.get_locker_config(locker_id)
        if not cfg:
            return None
        return (cfg.get("backend_region") or cfg.get("region") or "").strip().upper() or None

    def get_lockers_by_region(self, region: str) -> Dict[str, Dict[str, Any]]:
        reg = (region or "").strip().upper()
        return {
            locker_id: cfg
            for locker_id, cfg in self.locker_registry.items()
            if (cfg.get("region") or "").strip().upper() == reg
        }

    def get_payment_methods_for_locker(self, locker_id: str) -> list[str]:
        cfg = self.get_locker_config(locker_id)
        if not cfg:
            return []
        methods = cfg.get("payment_methods") or []
        return [str(m).strip().upper() for m in methods if str(m).strip()]

    def get_channels_for_locker(self, locker_id: str) -> list[str]:
        cfg = self.get_locker_config(locker_id)
        if not cfg:
            return []
        channels = cfg.get("channels") or []
        return [str(c).strip().upper() for c in channels if str(c).strip()]

    def is_locker_active(self, locker_id: str) -> bool:
        cfg = self.get_locker_config(locker_id)
        if not cfg:
            return False
        return bool(cfg.get("active", False))


settings = Settings()

# Compatibilidade com imports antigos
SQLITE_PATH = settings.SQLITE_PATH
IDEMPOTENCY_TTL_SEC = settings.IDEMPOTENCY_TTL_SEC
DEVICE_FP_VERSION = settings.DEVICE_FP_VERSION
GATEWAY_ID = settings.GATEWAY_ID
GATEWAY_LOG_DIR = settings.GATEWAY_LOG_DIR
LOG_HASH_SALT = settings.LOG_HASH_SALT

BACKEND_SP = settings.BACKEND_SP
BACKEND_PT = settings.BACKEND_PT
REGIONAL_BACKENDS = settings.REGIONAL_BACKENDS
REDIS_HOST = settings.REDIS_HOST
MQTT_HOST = settings.MQTT_HOST
ANTIFRAUD_ACTIVE_PEPPER_VERSION = settings.ANTIFRAUD_ACTIVE_PEPPER_VERSION
ANTIFRAUD_PEPPER_V1 = settings.ANTIFRAUD_PEPPER_V1
ANTIFRAUD_PEPPER_V2 = settings.ANTIFRAUD_PEPPER_V2
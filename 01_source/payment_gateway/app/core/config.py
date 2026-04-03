# 01_source/payment_gateway/app/core/config.py
# 02/04/2026 v4 - Global Market Support + startup hardening
# veja fim do arquivo

import json
import os
from functools import cached_property
from typing import Any, Dict, Optional, List, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RegionCode(str, Enum):
    """Códigos de região suportados globalmente"""
    # América Latina
    BR = "BR"
    SP = "SP"
    RJ = "RJ"
    MG = "MG"
    RS = "RS"
    BA = "BA"
    MX = "MX"
    AR = "AR"
    CO = "CO"
    CL = "CL"
    PE = "PE"
    EC = "EC"
    UY = "UY"
    PY = "PY"
    BO = "BO"
    VE = "VE"
    CR = "CR"
    PA = "PA"
    DO = "DO"

    # América do Norte
    US_NY = "US_NY"
    US_CA = "US_CA"
    US_TX = "US_TX"
    US_FL = "US_FL"
    US_IL = "US_IL"
    CA_ON = "CA_ON"
    CA_QC = "CA_QC"
    CA_BC = "CA_BC"

    # Europa Ocidental
    PT = "PT"
    ES = "ES"
    FR = "FR"
    DE = "DE"
    UK = "UK"
    IT = "IT"
    NL = "NL"
    BE = "BE"
    CH = "CH"
    SE = "SE"
    NO = "NO"
    DK = "DK"
    FI = "FI"
    IE = "IE"
    AT = "AT"

    # Europa Oriental
    PL = "PL"
    CZ = "CZ"
    GR = "GR"
    HU = "HU"
    RO = "RO"
    RU = "RU"
    TR = "TR"

    # África
    ZA = "ZA"
    NG = "NG"
    KE = "KE"
    EG = "EG"
    MA = "MA"
    GH = "GH"
    SN = "SN"
    CI = "CI"
    TZ = "TZ"
    UG = "UG"
    RW = "RW"
    MZ = "MZ"
    AO = "AO"
    DZ = "DZ"
    TN = "TN"

    # Ásia - Leste Asiático
    CN = "CN"
    JP = "JP"
    KR = "KR"

    # Ásia - Sudeste Asiático
    TH = "TH"
    ID = "ID"
    SG = "SG"
    PH = "PH"
    VN = "VN"
    MY = "MY"

    # Oriente Médio
    AE = "AE"
    SA = "SA"
    QA = "QA"
    KW = "KW"
    BH = "BH"
    OM = "OM"
    JO = "JO"

    # Oceania
    AU = "AU"
    NZ = "NZ"


class Settings:
    # ------------------------------------------------------------------
    # Runtime (fonte única para lockers)
    # ------------------------------------------------------------------
    RUNTIME_BASE_URL: str = os.getenv(
        "RUNTIME_BASE_URL",
        os.getenv("LOCKER_RUNTIME_INTERNAL", "http://backend_runtime:8000"),
    ).rstrip("/")

    INTERNAL_SERVICE_TOKEN: Optional[str] = (
        os.getenv("INTERNAL_SERVICE_TOKEN")
        or os.getenv("INTERNAL_TOKEN")
        or os.getenv("ORDER_INTERNAL_TOKEN")
    )

    # ------------------------------------------------------------------
    # Backends regionais expandidos
    # ------------------------------------------------------------------
    # América Latina
    BACKEND_BR: str = os.getenv("BACKEND_BR", RUNTIME_BASE_URL)
    BACKEND_SP: str = os.getenv("BACKEND_SP", RUNTIME_BASE_URL)
    BACKEND_RJ: str = os.getenv("BACKEND_RJ", RUNTIME_BASE_URL)
    BACKEND_MG: str = os.getenv("BACKEND_MG", RUNTIME_BASE_URL)
    BACKEND_RS: str = os.getenv("BACKEND_RS", RUNTIME_BASE_URL)
    BACKEND_BA: str = os.getenv("BACKEND_BA", RUNTIME_BASE_URL)
    BACKEND_MX: str = os.getenv("BACKEND_MX", RUNTIME_BASE_URL)
    BACKEND_AR: str = os.getenv("BACKEND_AR", RUNTIME_BASE_URL)
    BACKEND_CO: str = os.getenv("BACKEND_CO", RUNTIME_BASE_URL)
    BACKEND_CL: str = os.getenv("BACKEND_CL", RUNTIME_BASE_URL)
    BACKEND_PE: str = os.getenv("BACKEND_PE", RUNTIME_BASE_URL)
    BACKEND_EC: str = os.getenv("BACKEND_EC", RUNTIME_BASE_URL)
    BACKEND_UY: str = os.getenv("BACKEND_UY", RUNTIME_BASE_URL)
    BACKEND_PY: str = os.getenv("BACKEND_PY", RUNTIME_BASE_URL)
    BACKEND_BO: str = os.getenv("BACKEND_BO", RUNTIME_BASE_URL)
    BACKEND_VE: str = os.getenv("BACKEND_VE", RUNTIME_BASE_URL)
    BACKEND_CR: str = os.getenv("BACKEND_CR", RUNTIME_BASE_URL)
    BACKEND_PA: str = os.getenv("BACKEND_PA", RUNTIME_BASE_URL)
    BACKEND_DO: str = os.getenv("BACKEND_DO", RUNTIME_BASE_URL)

    # América do Norte
    BACKEND_US_NY: str = os.getenv("BACKEND_US_NY", RUNTIME_BASE_URL)
    BACKEND_US_CA: str = os.getenv("BACKEND_US_CA", RUNTIME_BASE_URL)
    BACKEND_US_TX: str = os.getenv("BACKEND_US_TX", RUNTIME_BASE_URL)
    BACKEND_US_FL: str = os.getenv("BACKEND_US_FL", RUNTIME_BASE_URL)
    BACKEND_US_IL: str = os.getenv("BACKEND_US_IL", RUNTIME_BASE_URL)
    BACKEND_CA_ON: str = os.getenv("BACKEND_CA_ON", RUNTIME_BASE_URL)
    BACKEND_CA_QC: str = os.getenv("BACKEND_CA_QC", RUNTIME_BASE_URL)
    BACKEND_CA_BC: str = os.getenv("BACKEND_CA_BC", RUNTIME_BASE_URL)

    # Europa
    BACKEND_PT: str = os.getenv("BACKEND_PT", RUNTIME_BASE_URL)
    BACKEND_ES: str = os.getenv("BACKEND_ES", RUNTIME_BASE_URL)
    BACKEND_FR: str = os.getenv("BACKEND_FR", RUNTIME_BASE_URL)
    BACKEND_DE: str = os.getenv("BACKEND_DE", RUNTIME_BASE_URL)
    BACKEND_UK: str = os.getenv("BACKEND_UK", RUNTIME_BASE_URL)
    BACKEND_IT: str = os.getenv("BACKEND_IT", RUNTIME_BASE_URL)
    BACKEND_NL: str = os.getenv("BACKEND_NL", RUNTIME_BASE_URL)
    BACKEND_BE: str = os.getenv("BACKEND_BE", RUNTIME_BASE_URL)
    BACKEND_CH: str = os.getenv("BACKEND_CH", RUNTIME_BASE_URL)
    BACKEND_SE: str = os.getenv("BACKEND_SE", RUNTIME_BASE_URL)
    BACKEND_NO: str = os.getenv("BACKEND_NO", RUNTIME_BASE_URL)
    BACKEND_DK: str = os.getenv("BACKEND_DK", RUNTIME_BASE_URL)
    BACKEND_FI: str = os.getenv("BACKEND_FI", RUNTIME_BASE_URL)
    BACKEND_IE: str = os.getenv("BACKEND_IE", RUNTIME_BASE_URL)
    BACKEND_AT: str = os.getenv("BACKEND_AT", RUNTIME_BASE_URL)
    BACKEND_PL: str = os.getenv("BACKEND_PL", RUNTIME_BASE_URL)
    BACKEND_CZ: str = os.getenv("BACKEND_CZ", RUNTIME_BASE_URL)
    BACKEND_GR: str = os.getenv("BACKEND_GR", RUNTIME_BASE_URL)
    BACKEND_HU: str = os.getenv("BACKEND_HU", RUNTIME_BASE_URL)
    BACKEND_RO: str = os.getenv("BACKEND_RO", RUNTIME_BASE_URL)
    BACKEND_RU: str = os.getenv("BACKEND_RU", RUNTIME_BASE_URL)
    BACKEND_TR: str = os.getenv("BACKEND_TR", RUNTIME_BASE_URL)

    # África
    BACKEND_ZA: str = os.getenv("BACKEND_ZA", RUNTIME_BASE_URL)
    BACKEND_NG: str = os.getenv("BACKEND_NG", RUNTIME_BASE_URL)
    BACKEND_KE: str = os.getenv("BACKEND_KE", RUNTIME_BASE_URL)
    BACKEND_EG: str = os.getenv("BACKEND_EG", RUNTIME_BASE_URL)
    BACKEND_MA: str = os.getenv("BACKEND_MA", RUNTIME_BASE_URL)
    BACKEND_GH: str = os.getenv("BACKEND_GH", RUNTIME_BASE_URL)
    BACKEND_SN: str = os.getenv("BACKEND_SN", RUNTIME_BASE_URL)
    BACKEND_CI: str = os.getenv("BACKEND_CI", RUNTIME_BASE_URL)
    BACKEND_TZ: str = os.getenv("BACKEND_TZ", RUNTIME_BASE_URL)
    BACKEND_UG: str = os.getenv("BACKEND_UG", RUNTIME_BASE_URL)
    BACKEND_RW: str = os.getenv("BACKEND_RW", RUNTIME_BASE_URL)
    BACKEND_MZ: str = os.getenv("BACKEND_MZ", RUNTIME_BASE_URL)
    BACKEND_AO: str = os.getenv("BACKEND_AO", RUNTIME_BASE_URL)
    BACKEND_DZ: str = os.getenv("BACKEND_DZ", RUNTIME_BASE_URL)
    BACKEND_TN: str = os.getenv("BACKEND_TN", RUNTIME_BASE_URL)

    # Ásia
    BACKEND_CN: str = os.getenv("BACKEND_CN", RUNTIME_BASE_URL)
    BACKEND_JP: str = os.getenv("BACKEND_JP", RUNTIME_BASE_URL)
    BACKEND_KR: str = os.getenv("BACKEND_KR", RUNTIME_BASE_URL)
    BACKEND_TH: str = os.getenv("BACKEND_TH", RUNTIME_BASE_URL)
    BACKEND_ID: str = os.getenv("BACKEND_ID", RUNTIME_BASE_URL)
    BACKEND_SG: str = os.getenv("BACKEND_SG", RUNTIME_BASE_URL)
    BACKEND_PH: str = os.getenv("BACKEND_PH", RUNTIME_BASE_URL)
    BACKEND_VN: str = os.getenv("BACKEND_VN", RUNTIME_BASE_URL)
    BACKEND_MY: str = os.getenv("BACKEND_MY", RUNTIME_BASE_URL)

    # Oriente Médio
    BACKEND_AE: str = os.getenv("BACKEND_AE", RUNTIME_BASE_URL)
    BACKEND_SA: str = os.getenv("BACKEND_SA", RUNTIME_BASE_URL)
    BACKEND_QA: str = os.getenv("BACKEND_QA", RUNTIME_BASE_URL)
    BACKEND_KW: str = os.getenv("BACKEND_KW", RUNTIME_BASE_URL)
    BACKEND_BH: str = os.getenv("BACKEND_BH", RUNTIME_BASE_URL)
    BACKEND_OM: str = os.getenv("BACKEND_OM", RUNTIME_BASE_URL)
    BACKEND_JO: str = os.getenv("BACKEND_JO", RUNTIME_BASE_URL)

    # Oceania
    BACKEND_AU: str = os.getenv("BACKEND_AU", RUNTIME_BASE_URL)
    BACKEND_NZ: str = os.getenv("BACKEND_NZ", RUNTIME_BASE_URL)

    # ------------------------------------------------------------------
    # Paths específicos por região
    # ------------------------------------------------------------------
    BACKEND_BR_PATH: str = os.getenv("BACKEND_BR_PATH", "")
    BACKEND_SP_PATH: str = os.getenv("BACKEND_SP_PATH", "")
    BACKEND_PT_PATH: str = os.getenv("BACKEND_PT_PATH", "")
    BACKEND_MX_PATH: str = os.getenv("BACKEND_MX_PATH", "")
    BACKEND_AR_PATH: str = os.getenv("BACKEND_AR_PATH", "")
    BACKEND_CO_PATH: str = os.getenv("BACKEND_CO_PATH", "")
    BACKEND_CL_PATH: str = os.getenv("BACKEND_CL_PATH", "")
    BACKEND_US_NY_PATH: str = os.getenv("BACKEND_US_NY_PATH", "")
    BACKEND_UK_PATH: str = os.getenv("BACKEND_UK_PATH", "")
    BACKEND_CN_PATH: str = os.getenv("BACKEND_CN_PATH", "")
    BACKEND_JP_PATH: str = os.getenv("BACKEND_JP_PATH", "")
    BACKEND_SG_PATH: str = os.getenv("BACKEND_SG_PATH", "")
    BACKEND_AE_PATH: str = os.getenv("BACKEND_AE_PATH", "")
    BACKEND_AU_PATH: str = os.getenv("BACKEND_AU_PATH", "")
    BACKEND_NG_PATH: str = os.getenv("BACKEND_NG_PATH", "")
    BACKEND_KE_PATH: str = os.getenv("BACKEND_KE_PATH", "")
    BACKEND_RU_PATH: str = os.getenv("BACKEND_RU_PATH", "")
    BACKEND_TR_PATH: str = os.getenv("BACKEND_TR_PATH", "")

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis_central")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")

    REDIS_REGIONAL_HOSTS: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # MQTT
    # ------------------------------------------------------------------
    MQTT_HOST: str = os.getenv("MQTT_HOST", "mqtt_broker")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_USERNAME: Optional[str] = os.getenv("MQTT_USERNAME")
    MQTT_PASSWORD: Optional[str] = os.getenv("MQTT_PASSWORD")
    MQTT_KEEPALIVE: int = int(os.getenv("MQTT_KEEPALIVE", "60"))

    # ------------------------------------------------------------------
    # SQLite
    # ------------------------------------------------------------------
    SQLITE_PATH: str = os.getenv(
        "GATEWAY_SQLITE_PATH",
        "/data/sqlite/gateway/events.db",
    )

    SQLITE_REGIONAL_PATHS: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Anti-fraude / auditoria
    # ------------------------------------------------------------------
    ANTIFRAUD_ACTIVE_PEPPER_VERSION: str = os.getenv(
        "ANTIFRAUD_ACTIVE_PEPPER_VERSION", "v1"
    )
    ANTIFRAUD_PEPPER_V1: Optional[str] = os.getenv("ANTIFRAUD_PEPPER_V1")
    ANTIFRAUD_PEPPER_V2: Optional[str] = os.getenv("ANTIFRAUD_PEPPER_V2")
    ANTIFRAUD_PEPPER_V3: Optional[str] = os.getenv("ANTIFRAUD_PEPPER_V3")
    LOG_HASH_SALT: Optional[str] = os.getenv("LOG_HASH_SALT")

    FRAUD_DETECTION_ENABLED_REGIONS: Set[str] = set()
    FRAUD_RULES_UPDATE_INTERVAL: int = int(os.getenv("FRAUD_RULES_UPDATE_INTERVAL", "300"))

    # ------------------------------------------------------------------
    # Idempotência
    # ------------------------------------------------------------------
    IDEMPOTENCY_TTL_SEC: int = int(os.getenv("IDEMPOTENCY_TTL_SEC", "86400"))
    IDEMPOTENCY_ENABLED: bool = os.getenv("IDEMPOTENCY_ENABLED", "true").lower() == "true"

    # ------------------------------------------------------------------
    # Device fingerprint
    # ------------------------------------------------------------------
    DEVICE_FP_VERSION: str = os.getenv("DEVICE_FP_VERSION", "v1_web")
    DEVICE_FP_ENABLED: bool = os.getenv("DEVICE_FP_ENABLED", "true").lower() == "true"

    # ------------------------------------------------------------------
    # Gateway
    # ------------------------------------------------------------------
    GATEWAY_ID: str = os.getenv("GATEWAY_ID", "payment_gateway_01")
    GATEWAY_LOG_DIR: str = os.getenv("GATEWAY_LOG_DIR", "/logs")
    GATEWAY_LOG_LEVEL: str = os.getenv("GATEWAY_LOG_LEVEL", "INFO")

    REQUEST_TIMEOUT_SEC: int = int(os.getenv("REQUEST_TIMEOUT_SEC", "30"))
    CONNECTION_TIMEOUT_SEC: int = int(os.getenv("CONNECTION_TIMEOUT_SEC", "10"))

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------
    WEBHOOK_RETRY_COUNT: int = int(os.getenv("WEBHOOK_RETRY_COUNT", "3"))
    WEBHOOK_RETRY_DELAY_SEC: int = int(os.getenv("WEBHOOK_RETRY_DELAY_SEC", "5"))
    WEBHOOK_TIMEOUT_SEC: int = int(os.getenv("WEBHOOK_TIMEOUT_SEC", "10"))

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
    RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "10"))

    REGIONAL_RATE_LIMITS: Dict[str, int] = {
        "SP": 100,
        "PT": 80,
        "CN": 200,
        "JP": 150,
        "US_NY": 120,
        "NG": 50,
        "AE": 100,
        "AU": 100,
    }

    # ------------------------------------------------------------------
    # Compatibilidade legada temporária
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
    LEGACY_LOCKER_ID_MX: Optional[str] = os.getenv("LOCKER_ID_MX")
    LEGACY_LOCKER_ID_AR: Optional[str] = os.getenv("LOCKER_ID_AR")
    LEGACY_LOCKER_ID_CN: Optional[str] = os.getenv("LOCKER_ID_CN")
    LEGACY_LOCKER_ID_JP: Optional[str] = os.getenv("LOCKER_ID_JP")
    LEGACY_LOCKER_ID_SG: Optional[str] = os.getenv("LOCKER_ID_SG")
    LEGACY_LOCKER_ID_AE: Optional[str] = os.getenv("LOCKER_ID_AE")
    LEGACY_LOCKER_ID_AU: Optional[str] = os.getenv("LOCKER_ID_AU")

    LOCKER_REGISTRY_JSON: str = os.getenv("LOCKER_REGISTRY_JSON", "").strip()

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    def _backend_value(self, attr_name: str) -> str:
        value = getattr(self, attr_name, self.RUNTIME_BASE_URL)
        return value or self.RUNTIME_BASE_URL

    def _path_value(self, attr_name: str) -> str:
        value = getattr(self, attr_name, "")
        return value or ""

    # ------------------------------------------------------------------
    # Propriedades calculadas
    # ------------------------------------------------------------------
    @property
    def REGIONAL_BACKENDS(self) -> Dict[str, str]:
        """Mapeamento de regiões para URLs de backend"""
        mapping = {
            # América Latina
            "BR": "BACKEND_BR",
            "SP": "BACKEND_SP",
            "RJ": "BACKEND_RJ",
            "MG": "BACKEND_MG",
            "RS": "BACKEND_RS",
            "BA": "BACKEND_BA",
            "MX": "BACKEND_MX",
            "AR": "BACKEND_AR",
            "CO": "BACKEND_CO",
            "CL": "BACKEND_CL",
            "PE": "BACKEND_PE",
            "EC": "BACKEND_EC",
            "UY": "BACKEND_UY",
            "PY": "BACKEND_PY",
            "BO": "BACKEND_BO",
            "VE": "BACKEND_VE",
            "CR": "BACKEND_CR",
            "PA": "BACKEND_PA",
            "DO": "BACKEND_DO",

            # América do Norte
            "US_NY": "BACKEND_US_NY",
            "US_CA": "BACKEND_US_CA",
            "US_TX": "BACKEND_US_TX",
            "US_FL": "BACKEND_US_FL",
            "US_IL": "BACKEND_US_IL",
            "CA_ON": "BACKEND_CA_ON",
            "CA_QC": "BACKEND_CA_QC",
            "CA_BC": "BACKEND_CA_BC",

            # Europa
            "PT": "BACKEND_PT",
            "ES": "BACKEND_ES",
            "FR": "BACKEND_FR",
            "DE": "BACKEND_DE",
            "UK": "BACKEND_UK",
            "IT": "BACKEND_IT",
            "NL": "BACKEND_NL",
            "BE": "BACKEND_BE",
            "CH": "BACKEND_CH",
            "SE": "BACKEND_SE",
            "NO": "BACKEND_NO",
            "DK": "BACKEND_DK",
            "FI": "BACKEND_FI",
            "IE": "BACKEND_IE",
            "AT": "BACKEND_AT",
            "PL": "BACKEND_PL",
            "CZ": "BACKEND_CZ",
            "GR": "BACKEND_GR",
            "HU": "BACKEND_HU",
            "RO": "BACKEND_RO",
            "RU": "BACKEND_RU",
            "TR": "BACKEND_TR",

            # África
            "ZA": "BACKEND_ZA",
            "NG": "BACKEND_NG",
            "KE": "BACKEND_KE",
            "EG": "BACKEND_EG",
            "MA": "BACKEND_MA",
            "GH": "BACKEND_GH",
            "SN": "BACKEND_SN",
            "CI": "BACKEND_CI",
            "TZ": "BACKEND_TZ",
            "UG": "BACKEND_UG",
            "RW": "BACKEND_RW",
            "MZ": "BACKEND_MZ",
            "AO": "BACKEND_AO",
            "DZ": "BACKEND_DZ",
            "TN": "BACKEND_TN",

            # Ásia
            "CN": "BACKEND_CN",
            "JP": "BACKEND_JP",
            "KR": "BACKEND_KR",
            "TH": "BACKEND_TH",
            "ID": "BACKEND_ID",
            "SG": "BACKEND_SG",
            "PH": "BACKEND_PH",
            "VN": "BACKEND_VN",
            "MY": "BACKEND_MY",

            # Oriente Médio
            "AE": "BACKEND_AE",
            "SA": "BACKEND_SA",
            "QA": "BACKEND_QA",
            "KW": "BACKEND_KW",
            "BH": "BACKEND_BH",
            "OM": "BACKEND_OM",
            "JO": "BACKEND_JO",

            # Oceania
            "AU": "BACKEND_AU",
            "NZ": "BACKEND_NZ",
        }

        backends = {region: self._backend_value(attr) for region, attr in mapping.items()}
        return {key: value for key, value in backends.items() if value}

    @property
    def REGIONAL_PATHS(self) -> Dict[str, str]:
        """Mapeamento de regiões para paths específicos"""
        mapping = {
            "BR": "BACKEND_BR_PATH",
            "SP": "BACKEND_SP_PATH",
            "PT": "BACKEND_PT_PATH",
            "MX": "BACKEND_MX_PATH",
            "AR": "BACKEND_AR_PATH",
            "CO": "BACKEND_CO_PATH",
            "CL": "BACKEND_CL_PATH",
            "US_NY": "BACKEND_US_NY_PATH",
            "UK": "BACKEND_UK_PATH",
            "CN": "BACKEND_CN_PATH",
            "JP": "BACKEND_JP_PATH",
            "SG": "BACKEND_SG_PATH",
            "AE": "BACKEND_AE_PATH",
            "AU": "BACKEND_AU_PATH",
            "NG": "BACKEND_NG_PATH",
            "KE": "BACKEND_KE_PATH",
            "RU": "BACKEND_RU_PATH",
            "TR": "BACKEND_TR_PATH",
        }
        return {region: self._path_value(attr) for region, attr in mapping.items()}

    @property
    def ALL_SUPPORTED_REGIONS(self) -> List[str]:
        """Lista de todas as regiões suportadas"""
        return [member.value for member in RegionCode]

    @property
    def ACTIVE_REGIONS(self) -> List[str]:
        """Regiões ativas (com backend configurado)"""
        return list(self.REGIONAL_BACKENDS.keys())

    def get_regional_url(self, region: str) -> str:
        """Obtém URL do backend para uma região específica"""
        reg = (region or "").upper().strip()

        if not reg:
            raise ValueError("Region cannot be empty")

        url = self.REGIONAL_BACKENDS.get(reg)
        if not url:
            logger.warning(
                "No backend URL configured for region %s, using runtime base URL",
                reg,
            )
            return self.RUNTIME_BASE_URL

        return url.rstrip("/")

    def get_regional_path(self, region: str) -> str:
        """Obtém path específico para uma região"""
        reg = (region or "").upper().strip()
        return self.REGIONAL_PATHS.get(reg, "")

    def get_regional_redis_host(self, region: str) -> str:
        """Obtém host Redis para região específica"""
        reg = (region or "").upper().strip()
        return self.REDIS_REGIONAL_HOSTS.get(reg, self.REDIS_HOST)

    def get_regional_sqlite_path(self, region: str) -> str:
        """Obtém path SQLite para região específica"""
        reg = (region or "").upper().strip()
        if reg in self.SQLITE_REGIONAL_PATHS:
            return self.SQLITE_REGIONAL_PATHS[reg]
        return f"/data/sqlite/gateway/events_{reg.lower()}.db"

    def get_legacy_locker_id(self, region: str) -> Optional[str]:
        """Obtém locker ID legado para região"""
        reg = (region or "").upper().strip()
        legacy_map = {
            "SP": self.LEGACY_LOCKER_ID_SP,
            "PT": self.LEGACY_LOCKER_ID_PT,
            "MX": self.LEGACY_LOCKER_ID_MX,
            "AR": self.LEGACY_LOCKER_ID_AR,
            "CN": self.LEGACY_LOCKER_ID_CN,
            "JP": self.LEGACY_LOCKER_ID_JP,
            "SG": self.LEGACY_LOCKER_ID_SG,
            "AE": self.LEGACY_LOCKER_ID_AE,
            "AU": self.LEGACY_LOCKER_ID_AU,
        }
        return legacy_map.get(reg)

    def get_rate_limit_for_region(self, region: str) -> int:
        """Obtém limite de taxa para região específica"""
        reg = (region or "").upper().strip()
        return self.REGIONAL_RATE_LIMITS.get(reg, self.RATE_LIMIT_REQUESTS_PER_MINUTE)

    @cached_property
    def locker_registry(self) -> Dict[str, Dict[str, Any]]:
        """
        Registry de lockers com suporte global.
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
                raise RuntimeError(
                    f"Configuração do locker {key} deve ser um objeto JSON."
                )
            normalized[key] = cfg

        return normalized

    def get_locker_config(self, locker_id: str) -> Optional[Dict[str, Any]]:
        """Obtém configuração de um locker específico"""
        normalized = str(locker_id or "").strip().upper()
        if not normalized:
            return None
        return self.locker_registry.get(normalized)

    def get_locker_region(self, locker_id: str) -> Optional[str]:
        """Obtém região de um locker"""
        cfg = self.get_locker_config(locker_id)
        if not cfg:
            return None
        return (cfg.get("region") or "").strip().upper() or None

    def get_locker_backend_region(self, locker_id: str) -> Optional[str]:
        """Obtém região de backend para um locker"""
        cfg = self.get_locker_config(locker_id)
        if not cfg:
            return None
        return (
            (cfg.get("backend_region") or cfg.get("region") or "")
            .strip()
            .upper()
            or None
        )

    def get_lockers_by_region(self, region: str) -> Dict[str, Dict[str, Any]]:
        """Obtém todos lockers de uma região"""
        reg = (region or "").strip().upper()
        return {
            locker_id: cfg
            for locker_id, cfg in self.locker_registry.items()
            if (cfg.get("region") or "").strip().upper() == reg
        }

    def get_payment_methods_for_locker(self, locker_id: str) -> List[str]:
        """Obtém métodos de pagamento suportados por um locker"""
        cfg = self.get_locker_config(locker_id)
        if not cfg:
            return []
        methods = cfg.get("payment_methods") or []
        return [str(m).strip().lower() for m in methods if str(m).strip()]

    def get_channels_for_locker(self, locker_id: str) -> List[str]:
        """Obtém canais suportados por um locker"""
        cfg = self.get_locker_config(locker_id)
        if not cfg:
            return []
        channels = cfg.get("channels") or []
        return [str(c).strip().lower() for c in channels if str(c).strip()]

    def is_locker_active(self, locker_id: str) -> bool:
        """Verifica se um locker está ativo"""
        cfg = self.get_locker_config(locker_id)
        if not cfg:
            return False
        return bool(cfg.get("active", False))

    def get_locker_timezone(self, locker_id: str) -> str:
        """Obtém timezone de um locker"""
        cfg = self.get_locker_config(locker_id)
        if not cfg:
            return "UTC"
        return cfg.get("timezone", "UTC")

    def requires_qr_for_locker(self, locker_id: str) -> bool:
        """Verifica se locker requer QR code"""
        cfg = self.get_locker_config(locker_id)
        if not cfg:
            return False
        return cfg.get("qr_required", False)

    def get_locker_max_slots(self, locker_id: str) -> int:
        """Obtém número máximo de slots de um locker"""
        cfg = self.get_locker_config(locker_id)
        if not cfg:
            return 100
        return cfg.get("max_slots", 100)


settings = Settings()

# ------------------------------------------------------------------
# Compatibilidade com imports antigos (mantido)
# ------------------------------------------------------------------
SQLITE_PATH = settings.SQLITE_PATH
IDEMPOTENCY_TTL_SEC = settings.IDEMPOTENCY_TTL_SEC
DEVICE_FP_VERSION = settings.DEVICE_FP_VERSION
GATEWAY_ID = settings.GATEWAY_ID
GATEWAY_LOG_DIR = settings.GATEWAY_LOG_DIR
LOG_HASH_SALT = settings.LOG_HASH_SALT

BACKEND_BR = settings.BACKEND_BR
BACKEND_SP = settings.BACKEND_SP
BACKEND_PT = settings.BACKEND_PT
REGIONAL_BACKENDS = settings.REGIONAL_BACKENDS
REGIONAL_PATHS = settings.REGIONAL_PATHS

REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT
MQTT_HOST = settings.MQTT_HOST
MQTT_PORT = settings.MQTT_PORT

ANTIFRAUD_ACTIVE_PEPPER_VERSION = settings.ANTIFRAUD_ACTIVE_PEPPER_VERSION
ANTIFRAUD_PEPPER_V1 = settings.ANTIFRAUD_PEPPER_V1
ANTIFRAUD_PEPPER_V2 = settings.ANTIFRAUD_PEPPER_V2
ANTIFRAUD_PEPPER_V3 = settings.ANTIFRAUD_PEPPER_V3

# ------------------------------------------------------------------
# Novas exports para compatibilidade com código atualizado
# ------------------------------------------------------------------
RUNTIME_BASE_URL = settings.RUNTIME_BASE_URL
INTERNAL_SERVICE_TOKEN = settings.INTERNAL_SERVICE_TOKEN
REDIS_DB = settings.REDIS_DB
REDIS_PASSWORD = settings.REDIS_PASSWORD
MQTT_USERNAME = settings.MQTT_USERNAME
MQTT_PASSWORD = settings.MQTT_PASSWORD
REQUEST_TIMEOUT_SEC = settings.REQUEST_TIMEOUT_SEC
CONNECTION_TIMEOUT_SEC = settings.CONNECTION_TIMEOUT_SEC
RATE_LIMIT_ENABLED = settings.RATE_LIMIT_ENABLED
WEBHOOK_RETRY_COUNT = settings.WEBHOOK_RETRY_COUNT


"""

1. Enum RegionCode
Lista completa de todas as regiões suportadas globalmente

Categorizado por continente/região

Fácil manutenção e referência

2. Backends Regionais Expandidos
Suporte para 50+ regiões

Configurações específicas por país/estado

Fallback para runtime base URL quando não configurado

3. Novas Configurações
Categoria	Configurações
Redis	Hosts regionais, password, database
MQTT	Username, password, keepalive
Anti-fraude	Pepper V3, regras por região
Rate Limiting	Limites específicos por região
Webhooks	Retry count, timeout, delay
Timeouts	Request e connection timeouts
4. Propriedades Dinâmicas
ALL_SUPPORTED_REGIONS
Lista todas as regiões do enum

ACTIVE_REGIONS
Apenas regiões com backend configurado

5. Métodos Regionais Aprimorados
python
get_regional_url(region)      # URL do backend regional
get_regional_path(region)     # Path específico
get_regional_redis_host(region) # Redis regional
get_regional_sqlite_path(region) # SQLite regional
get_rate_limit_for_region(region) # Rate limit
6. Configuração de Lockers Aprimorada
Novos campos no JSON de configuração:

json
{
    "LOCKER_CN_001": {
        "region": "CN",
        "timezone": "Asia/Shanghai",
        "max_slots": 200,
        "qr_required": true,
        "payment_methods": ["alipay", "wechat_pay"]
    }
}
7. Rate Limiting por Região
Região	Requests/Minuto
China (CN)	200
Japão (JP)	150
EUA (US_NY)	120
Brasil (SP)	100
Nigéria (NG)	50
8. Legacy Support Mantido
Variáveis antigas preservadas

Métodos de compatibilidade

Transição suave

9. Timeouts e Performance
Request timeout: 30s (configurável)

Connection timeout: 10s

Webhook timeout: 10s

Retry mechanism configurável

10. Segurança Aprimorada
Redis password support

MQTT authentication

Pepper versions for fraud detection

Internal service token validation

11. Logging e Monitoramento
Gateway log level configurável

Log directory configurável por região

Fraude rules update interval

12. Extensibilidade
Fácil adição de novas regiões

Configurações herdáveis

Fallbacks inteligentes

Cache de propriedades computadas

"""
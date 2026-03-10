# app/core/config.py
import os
from typing import Dict, Optional

# Configurações básicas
class Settings:
    # Backends regionais
    BACKEND_SP: str = os.getenv("BACKEND_SP", "http://backend_sp:8000") # intenal
    BACKEND_PT: str = os.getenv("BACKEND_PT", "http://backend_pt:8000") # internal
    
    # Paths dos endpoints regionais
    BACKEND_SP_PATH: str = os.getenv("BACKEND_SP_PATH", "")
    BACKEND_PT_PATH: str = os.getenv("BACKEND_PT_PATH", "")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis_sp")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    
    # MQTT
    MQTT_HOST: str = os.getenv("MQTT_HOST", "mqtt_broker")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))
    
    # SQLite
    SQLITE_PATH: str = os.getenv("GATEWAY_SQLITE_PATH", "/data/sqlite/gateway/events.db")
    
    # Anti-fraude
    ANTIFRAUD_ACTIVE_PEPPER_VERSION: str = os.getenv("ANTIFRAUD_ACTIVE_PEPPER_VERSION", "v1")
    ANTIFRAUD_PEPPER_V1: Optional[str] = os.getenv("ANTIFRAUD_PEPPER_V1")
    ANTIFRAUD_PEPPER_V2: Optional[str] = os.getenv("ANTIFRAUD_PEPPER_V2")
    LOG_HASH_SALT: Optional[str] = os.getenv("LOG_HASH_SALT")
    
    # Idempotência
    IDEMPOTENCY_TTL_SEC: int = int(os.getenv("IDEMPOTENCY_TTL_SEC", "86400"))
    
    # Device fingerprint
    DEVICE_FP_VERSION: str = os.getenv("DEVICE_FP_VERSION", "v1_web")
    
    # 🔥 PROPRIEDADES FALTANDO (adicione estas linhas)
    GATEWAY_ID: str = os.getenv("GATEWAY_ID", "payment_gateway_01")
    GATEWAY_LOG_DIR: str = os.getenv("GATEWAY_LOG_DIR", "/logs")

    @property
    def REGIONAL_BACKENDS(self) -> Dict[str, str]:
        """Retorna dicionário com backends por região"""
        return {
            "SP": self.BACKEND_SP,
            "PT": self.BACKEND_PT,
        }
    
    @property
    def REGIONAL_PATHS(self) -> Dict[str, str]:
        """Retorna dicionário com paths por região"""
        return {
            "SP": self.BACKEND_SP_PATH,
            "PT": self.BACKEND_PT_PATH,
        }
    
    def get_regional_url(self, region: str) -> str:
        reg = (region or "").upper()
        if reg == "SP":
            return self.BACKEND_SP.rstrip("/")
        if reg == "PT":
            return self.BACKEND_PT.rstrip("/")
        raise ValueError(f"Unknown region: {region}")

    # 🔥 Configurações para lockers por região - Diferentes lockers por região
    DEFAULT_LOCKER_ID: str = None  # Locker fallback se não especificado
    
    # Lockers específicos por região (podem ser definidos via env)
    # Exemplo: LOCKER_ID_SP="CACIFO-SP-042", LOCKER_ID_PT="CACIFO-PT-015"
    @property
    def locker_id_sp(self) -> str | None:
        return os.getenv("LOCKER_ID_SP")
    
    @property
    def locker_id_pt(self) -> str | None:
        return os.getenv("LOCKER_ID_PT")
    
    # Método helper para obter locker_id por região
    def get_locker_id(self, region: str) -> str | None:
        """Retorna locker_id configurado para a região ou None"""
        env_var = f"LOCKER_ID_{region.upper()}"
        return os.getenv(env_var)

# Instância global das configurações
settings = Settings()

# 🔥 VARIÁVEIS DE COMPATIBILIDADE (para imports antigos)
SQLITE_PATH = settings.SQLITE_PATH
IDEMPOTENCY_TTL_SEC = settings.IDEMPOTENCY_TTL_SEC
DEVICE_FP_VERSION = settings.DEVICE_FP_VERSION
GATEWAY_ID = settings.GATEWAY_ID
GATEWAY_LOG_DIR = settings.GATEWAY_LOG_DIR
LOG_HASH_SALT = settings.LOG_HASH_SALT

# Para compatibilidade com imports antigos
BACKEND_SP = settings.BACKEND_SP
BACKEND_PT = settings.BACKEND_PT
REGIONAL_BACKENDS = settings.REGIONAL_BACKENDS
REDIS_HOST = settings.REDIS_HOST
MQTT_HOST = settings.MQTT_HOST
ANTIFRAUD_ACTIVE_PEPPER_VERSION = settings.ANTIFRAUD_ACTIVE_PEPPER_VERSION
ANTIFRAUD_PEPPER_V1 = settings.ANTIFRAUD_PEPPER_V1
ANTIFRAUD_PEPPER_V2 = settings.ANTIFRAUD_PEPPER_V2
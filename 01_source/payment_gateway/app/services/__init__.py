# 01_source/payment_gateway/app/services/__init__.py
# 03/04/2026 - FINAL FIX (alinhado com código real do projeto)

"""
Services layer — versão FINAL alinhada com:

✔ runtime canônico
✔ nova matriz de pagamento
✔ services reais (sem funções fantasmas)
✔ compatível com routers existentes
"""

# ============================
# FLOW PRINCIPAL
# ============================

from .payment_service import process_payment

# ============================
# SERVICES REAIS
# ============================

# antifraude
from .antifraud_service import check_antifraud

# device / idempotência
from .device_registry_service import DeviceRegistryService
from .idempotency_service import IdempotencyService

# runtime / locker
from .locker_backend_client import LockerBackendClient

# risco (CORRETO)
from .risk_events_service import RiskEventsService

# sqlite
from .sqlite_service import SQLiteService

# ============================
# EXPORTS
# ============================

__all__ = [
    # principal
    "process_payment",

    # antifraude
    "check_antifraud",

    # services reais
    "DeviceRegistryService",
    "IdempotencyService",
    "LockerBackendClient",
    "RiskEventsService",
    "SQLiteService",
]
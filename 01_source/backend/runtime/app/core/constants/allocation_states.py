# 01_source/backend/runtime/app/core/constants/allocation_states.py
"""
Constantes para order / allocation domain
✔ KIOSK vs ONLINE consistentes
•	KIOSK usa slot_state 
•	ONLINE usa allocation_state 
•	ambos convergem via eventos 

estado de alocação/pedido (order domain)

removida: COMMITTED
normalizadas: nomes

Regra: 👉 frontend NÃO deve depender diretamente de constants backend

O correto é: frontend ← API → backend
Nunca: frontend → constants backend

STATE DE HARDWARE ≠ STATE DE PEDIDO
"""

from typing import Final, Tuple, Literal

AllocationState = Literal[
    "RESERVED_PENDING_PAYMENT",
    "PAID_PENDING_PICKUP",
    "PICKUP_COMPLETED",
    "EXPIRED",
    "CANCELLED",
]

ALLOCATION_ACTIVE_STATES: Final[Tuple[str, ...]] = (
    "RESERVED_PENDING_PAYMENT",
    "PAID_PENDING_PICKUP",
)

ALLOCATION_TERMINAL_STATES: Final[Tuple[str, ...]] = (
    "PICKUP_COMPLETED",
    "EXPIRED",
    "CANCELLED",
)
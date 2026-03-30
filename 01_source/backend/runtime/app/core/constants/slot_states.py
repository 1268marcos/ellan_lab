# 01_source/backend/runtime/app/core/constants/slot_states.py
"""
Constantes para runtime (locker físico)
✔ KIOSK vs ONLINE consistentes
•	KIOSK usa slot_state 
•	ONLINE usa allocation_state 
•	ambos convergem via eventos 

Estado de slot físico (locker runtime)

Regra: 👉 frontend NÃO deve depender diretamente de constants backend

O correto é: frontend ← API → backend
Nunca: frontend → constants backend

STATE DE HARDWARE ≠ STATE DE PEDIDO
"""

from typing import Final, Tuple, Literal

# ============================================================================
# SLOTS (Gavetas) - Estados do runtime/hardware
# ============================================================================

SLOT_STATES: Final[Tuple[str, ...]] = (
    "AVAILABLE",
    "RESERVED",
    "PAID_PENDING_PICKUP",
    "OUT_OF_STOCK",
)

SlotState = Literal[
    "AVAILABLE",
    "RESERVED",
    "PAID_PENDING_PICKUP",
    "OUT_OF_STOCK",
]

DOOR_ACTIVE_STATES: Final[Tuple[str, ...]] = (
    "RESERVED",
    "PAID_PENDING_PICKUP",
)

SLOT_OCCUPIED_STATES: Final[Tuple[str, ...]] = (
    "RESERVED",
    "PAID_PENDING_PICKUP",
)

DEFAULT_MIN_SLOT: Final[int] = 1


def is_door_active(state: str) -> bool:
    return state in DOOR_ACTIVE_STATES


def is_slot_available(state: str) -> bool:
    return state == "AVAILABLE"


def is_slot_occupied(state: str) -> bool:
    return state in SLOT_OCCUPIED_STATES
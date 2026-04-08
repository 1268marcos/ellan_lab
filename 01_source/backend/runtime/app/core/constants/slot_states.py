# 01_source/backend/runtime/app/core/constants/slot_states.py
# 08/04/2026 - explicação da matrix de estados para SLOT_STATES

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

Ao ocorrer: (veja a mudança para o SLOT_STATE)
- expiração de pré-pagamento: AVAILABLE
- retirada concluída: OUT_OF_STOCK
- produto pago mas não retirado em 2h: não pode ir automaticamente para OUT_OF_STOCK, porque o item ainda está lá, logo, passa para AVAILABLE

"""

from typing import Final, Tuple, Literal

# ============================================================================
# SLOTS (Gavetas) - Estados do runtime/hardware
# ============================================================================

SLOT_STATES: Final[Tuple[str, ...]] = (
    "AVAILABLE",           # há produto naquela gaveta e ele pode ser vendido
    "RESERVED",            # há produto, mas reservado
    "PAID_PENDING_PICKUP", # há produto, pago, aguardando retirada
    "OUT_OF_STOCK",        # a gaveta ficou sem item vendável porque o item unitário saiu dali
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
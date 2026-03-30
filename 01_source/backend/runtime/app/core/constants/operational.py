# 01_source/backend/runtime/app/core/constants/operational.py
"""
Constantes operacionais do sistema de lockers.
✔ KIOSK vs ONLINE consistentes
•	KIOSK usa slot_state 
•	ONLINE usa allocation_state 
•	ambos convergem via eventos 

Regra: 👉 frontend NÃO deve depender diretamente de constants backend

O correto é: frontend ← API → backend
Nunca: frontend → constants backend

STATE DE HARDWARE ≠ STATE DE PEDIDO
"""
from typing import Final

# Tempo de expiração da seleção de gaveta no frontend (segundos)
SLOT_SELECTION_TIMEOUT_SEC: Final[int] = 45

# ⚠️ aqui precisa alinhar com lifecycle service
# Tempo padrão para retirada após pagamento (segundos)
DEFAULT_PICKUP_DEADLINE_SEC: Final[int] = 7200 # 2horas X 60 minutos X 60 segundos

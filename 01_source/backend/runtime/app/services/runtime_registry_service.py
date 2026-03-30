# 01_source/backend/runtime/app/services/runtime_registry_service.py
"""
Responsável por consultar a fonte central de cadastro/configuração dos lockers.

No início pode ter fallback simples.
Depois deve buscar do banco central.
"""

def get_locker_runtime_context(locker_id: str) -> dict:
    # Stub inicial.
    # Depois buscar do Postgres central / registry real.
    return {
        "locker_id": locker_id,
        "machine_id": locker_id,
        "region": locker_id.split("-")[0] if "-" in locker_id else "UNKNOWN",
        "slot_ids": list(range(1, 25)),
    }
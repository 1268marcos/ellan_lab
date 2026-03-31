# 01_source/backend/runtime/app/core/mqtt_topics.py

from __future__ import annotations

"""
Responsável por gerar tópicos MQTT de forma dinâmica 
por locker/região, em vez de depender de constantes globais por processo.
"""


def door_command_topic(*, region: str, locker_id: str | None = None) -> str:
    """
    Mantém compatibilidade inicial com o padrão legado por região,
    mas já aceita evolução futura por locker.
    """
    region = str(region or "").strip().upper()
    if not region:
        region = "UNKNOWN"

    # Compatibilidade legada:
    return f"locker/{region}/doors/cmd"


def light_command_topic(*, region: str, locker_id: str | None = None) -> str:
    region = str(region or "").strip().upper()
    if not region:
        region = "UNKNOWN"

    # Compatibilidade legada:
    return f"locker/{region}/doors/light/cmd"
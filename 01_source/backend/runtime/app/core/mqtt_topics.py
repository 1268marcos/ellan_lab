# 01_source/backend/runtime/app/core/mqtt_topics.py
"""
Responsável por gerar tópicos MQTT de forma dinâmica 
por locker/região, em vez de depender de constantes globais por processo.
"""

def door_command_topic(region: str) -> str:
    return f"locker/{region}/doors/cmd"


def door_light_topic(region: str) -> str:
    return f"locker/{region}/doors/light/cmd"
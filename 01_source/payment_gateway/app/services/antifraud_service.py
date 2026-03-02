import random

def check_antifraud(regiao: str, metodo: str, valor: float) -> tuple[bool, str]:
    # Regras simples de simulação
    if valor <= 0:
        return False, "valor_invalido"

    # Simula risco maior em valores altos
    if valor > 500 and random.random() < 0.30:
        return False, "alto_valor"

    # Simula risco para cartão com pequena chance
    if metodo.upper() in ["CARTAO", "CARD"] and random.random() < 0.10:
        return False, "risco_cartao"

    return True, "ok"

# 01_source/payment_gateway/app/core/hashing.py
# 07/04/2026 - ajuste canonical_json para aceitar objetos como datetime

import json
import hashlib
from typing import Any, Dict


# def canonical_json(obj: Dict[str, Any]) -> str:
#     """
#     JSON canônico para hash/idempotency: ordena chaves e remove espaços.
#     """
#     return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def canonical_json(obj):
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )

def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def sha256_prefixed(data: str) -> str:
    return f"sha256:{sha256_hex(data)}"


def hash_with_pepper(value: str, pepper: str) -> str:
    # Normaliza entradas e aplica pepper
    base = f"{pepper}::{value.strip()}"
    return sha256_prefixed(base)


def hash_with_pepper_version(value: str, pepper: str, pepper_version: str) -> str:
    """
    Retorna hash versionado, ex: "v1:sha256:abcd..."
    Isso permite rotação de pepper sem quebrar todo o histórico.
    """
    base = f"{pepper}::{value.strip()}"
    return f"{pepper_version}:{sha256_prefixed(base)}"
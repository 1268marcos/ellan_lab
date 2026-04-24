"""Cifragem reversível (Fernet) para PII fiscal em repouso — não substitui hash de senha."""

from __future__ import annotations

import logging
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import String, TypeDecorator

logger = logging.getLogger(__name__)

_fernet_cached: Fernet | None = None
_fernet_init_done: bool = False


def _fernet() -> Fernet | None:
    global _fernet_cached, _fernet_init_done
    if _fernet_init_done:
        return _fernet_cached
    _fernet_init_done = True
    from app.core.config import settings

    raw = (getattr(settings, "fiscal_pii_fernet_key", None) or "").strip()
    if not raw:
        _fernet_cached = None
        return None
    try:
        _fernet_cached = Fernet(raw.encode("ascii"))
    except Exception as exc:
        logger.error("fiscal_pii_fernet_key_invalid err=%s", exc)
        _fernet_cached = None
    return _fernet_cached


def encrypt_pii_field(plain: str | None) -> str | None:
    if plain is None or plain == "":
        return None
    f = _fernet()
    if f is None:
        logger.warning("fiscal_pii_fernet_key_missing_storing_plaintext_once")
        return plain
    return f.encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt_pii_field(stored: str | None) -> str | None:
    if stored is None or stored == "":
        return None
    f = _fernet()
    if f is None:
        return stored
    try:
        return f.decrypt(stored.encode("ascii")).decode("utf-8")
    except InvalidToken:
        return stored
    except Exception:
        return stored


class EncryptedPIIString(TypeDecorator):
    """Armazena texto cifrado Fernet; leitura transparente para o modelo ORM."""

    impl = String(1024)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect) -> str | None:
        if value is None:
            return None
        s = str(value).strip()
        if not s:
            return None
        return encrypt_pii_field(s)

    def process_result_value(self, value: Any, dialect) -> str | None:
        if value is None:
            return None
        return decrypt_pii_field(str(value))

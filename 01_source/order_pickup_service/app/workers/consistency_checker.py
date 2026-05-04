from __future__ import annotations

import json
import logging
from typing import Any, Iterable

logger = logging.getLogger(__name__)


def compare_schemas(
    legacy: dict[str, Any],
    remote: dict[str, Any],
    keys: Iterable[str],
) -> list[str]:
    """Compara apenas chaves declaradas; retorna lista de divergências (vazia = match)."""
    divergences: list[str] = []
    for k in keys:
        if legacy.get(k) != remote.get(k):
            divergences.append(k)
    return divergences


def log_divergences(*, context: str, divergences: list[str], legacy: dict[str, Any], remote: dict[str, Any]) -> None:
    if not divergences:
        return
    logger.warning(
        "shadow_mode divergence context=%s keys=%s legacy=%s remote=%s",
        context,
        divergences,
        json.dumps(legacy, default=str)[:2000],
        json.dumps(remote, default=str)[:2000],
    )

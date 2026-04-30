"""Pytest: permite rodar testes que usam Postgres no host com Docker mapeando a porta.

Defina ``ELL_USE_LOCAL_DOCKER_PG=1`` (ou ``true``) para usar ``127.0.0.1`` e porta
``5435`` (padrão do compose: postgres_central 5435:5432), em vez de ``postgres_central``
(DNS interno da rede Docker, inacessível do host).
"""

from __future__ import annotations

import os

if os.environ.get("ELL_USE_LOCAL_DOCKER_PG", "").lower() in ("1", "true", "yes"):
    os.environ.setdefault("POSTGRES_HOST", "127.0.0.1")
    os.environ.setdefault("POSTGRES_PORT", "5435")

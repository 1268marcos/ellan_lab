"""Schemas do portal COO (operações)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CooPortalMetaOut(BaseModel):
    """Metadados do portal — base para o front e health de feature."""

    portal: str = Field(description="Identificador fixo do portal")
    title: str = Field(description="Nome amigável")
    api_version: str = Field(description="Versão lógica da API COO")
    as_of: str = Field(description="Timestamp UTC ISO do payload")

"""Lógica de negócio do portal COO (camada serviço)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.coo import CooPortalMetaOut


def build_portal_meta(*, api_version: str = "0.1.0") -> CooPortalMetaOut:
    now = datetime.now(timezone.utc)
    return CooPortalMetaOut(
        portal="coo",
        title="Portal COO",
        api_version=api_version,
        as_of=now.isoformat(),
    )

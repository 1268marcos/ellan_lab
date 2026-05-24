from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FinanceSyncOut(BaseModel):
    synced_at: datetime
    finance_base_url: str
    finance_catalog_total: int = 0
    finance_sync_triggered: bool = False
    players_created: int = 0
    players_updated: int = 0
    players_deactivated: int = 0
    segments_upserted: int = 0
    relations_created: int = 0
    relations_skipped: int = 0
    warnings: list[str] = Field(default_factory=list)


class FinanceSyncStatusOut(BaseModel):
    finance_admin_base_url: str
    finance_admin_sync_enabled: bool
    last_sync: FinanceSyncOut | None = None

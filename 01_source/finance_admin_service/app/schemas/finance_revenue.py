from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class RevenueScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    partner_id: str
    source_type: str
    source_id: str
    total_cents: int
    recognized_cents: int
    deferred_cents: int
    recognition_method: str
    period_start: date
    period_end: date
    currency: str
    status: str
    created_at: datetime


class RevenueScheduleListOut(BaseModel):
    items: list[RevenueScheduleOut]
    total: int


class RevenueEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    schedule_id: str
    partner_id: str
    recognition_date: date
    amount_cents: int
    entry_status: str
    fiscal_synced: bool
    created_at: datetime


class RevenueEntryListOut(BaseModel):
    items: list[RevenueEntryOut]
    total: int


class RevenueRunOut(BaseModel):
    entries_created: int
    schedules_updated: int
    fiscal: dict | None = None


class JobRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_code: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    result_json: str
    error_message: str | None


class JobRunListOut(BaseModel):
    items: list[JobRunOut]
    total: int


class JobExecuteOut(BaseModel):
    job_run_id: str
    job_code: str
    status: str
    recomputed: int | None = None
    average_score: float | None = None


class FiscalEmitOut(BaseModel):
    invoice_id: str
    fiscal_status: str | None = None
    access_key: str | None = None
    pdf_url: str | None = None
    mode: str | None = None
    already_issued: bool = False

"""SLA fornecedores — agrega eventos conhecidos e stubs onde não há dado persistido."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.logistics_tracking import LogisticsPartner, SlaBreachEvent
from app.schemas.coo import ComplianceReportRow, PenaltyRecord, SLASupplierRow, SLAViolations


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _period_start(period: str) -> datetime:
    p = (period or "month").strip().lower()
    now = _utc_now()
    if p == "week":
        return now - timedelta(days=7)
    if p == "quarter":
        return now - timedelta(days=90)
    return now - timedelta(days=30)


class SLAService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_sla_by_supplier(self, period: str) -> SLAViolations:
        db = self._db
        now = _utc_now()
        start = _period_start(period)

        breach_counts = (
            db.query(SlaBreachEvent.logistics_partner_id, func.count(SlaBreachEvent.id))
            .filter(SlaBreachEvent.detected_at >= start)
            .group_by(SlaBreachEvent.logistics_partner_id)
            .all()
        )
        breach_map = {str(pid): int(c) for pid, c in breach_counts if pid}

        partners = db.query(LogisticsPartner.id).all()
        suppliers: list[SLASupplierRow] = []
        for (pid,) in partners:
            sid = str(pid)
            breaches = breach_map.get(sid, 0)
            on_time = max(0.0, 100.0 - min(100.0, float(breaches) * 5.0))
            suppliers.append(
                SLASupplierRow(
                    supplier_id=sid,
                    supplier_label=sid,
                    on_time_pct=round(on_time, 2),
                    breach_count=breaches,
                )
            )

        if not suppliers and breach_map:
            for sid, breaches in breach_map.items():
                on_time = max(0.0, 100.0 - min(100.0, float(breaches) * 5.0))
                suppliers.append(
                    SLASupplierRow(
                        supplier_id=sid,
                        supplier_label=sid,
                        on_time_pct=round(on_time, 2),
                        breach_count=breaches,
                    )
                )

        return SLAViolations(period=(period or "month").strip().lower(), as_of=now.isoformat(), suppliers=suppliers)

    def get_applied_penalties(
        self,
        supplier_id: str | None,
        start_date: datetime | None,
        end_date: datetime | None,
    ) -> list[PenaltyRecord]:
        del supplier_id, start_date, end_date
        return []

    def get_compliance_reports(self, period: str) -> list[ComplianceReportRow]:
        db = self._db
        start = _period_start(period)
        rows = db.query(LogisticsPartner.id).all()
        out: list[ComplianceReportRow] = []
        for (pid,) in rows:
            breaches = (
                db.query(func.count(SlaBreachEvent.id))
                .filter(
                    SlaBreachEvent.logistics_partner_id == pid,
                    SlaBreachEvent.detected_at >= start,
                )
                .scalar()
                or 0
            )
            score = max(0.0, 100.0 - min(100.0, int(breaches) * 3.0))
            out.append(
                ComplianceReportRow(
                    supplier_id=str(pid),
                    compliance_score=round(score, 2),
                    audit_notes=None,
                )
            )
        return out

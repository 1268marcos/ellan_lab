from __future__ import annotations

from sqlalchemy.orm import Session

from app.services import reconciliation_service


def run_nightly(session_factory: type, db: Session | None = None) -> list[dict]:
    if db is not None:
        return reconciliation_service.reconcile_all(db)
    s = session_factory()
    try:
        return reconciliation_service.reconcile_all(s)
    finally:
        s.close()

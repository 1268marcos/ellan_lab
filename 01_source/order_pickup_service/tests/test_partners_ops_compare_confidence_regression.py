from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.auth_dep import get_current_public_user
from app.core.db import Base, get_db
from app.models.ops_action_audit import OpsActionAudit
from app.routers.partners import router as partners_router


class _OpsUser:
    id = "user-ops-audit-001"
    full_name = "Ops Auditor"
    email = "ops-auditor@example.com"
    is_active = True
    email_verified = True


def _prepare_db():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(
        f"sqlite:///{path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    Session = sessionmaker(bind=engine, future=True)
    Base.metadata.create_all(bind=engine, tables=[OpsActionAudit.__table__])
    return engine, Session, path


def _build_client(Session, monkeypatch):
    app = FastAPI()
    app.include_router(partners_router)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_public_user] = lambda: _OpsUser()
    monkeypatch.setattr("app.core.auth_dep.user_has_any_role", lambda *args, **kwargs: True)
    return TestClient(app)


def _seed_audit_rows(Session, *, current_count: int, previous_count: int, partner_id: str):
    now_to = datetime(2026, 1, 10, tzinfo=timezone.utc)
    now_from = now_to - timedelta(days=7)
    previous_to = now_from
    previous_from = previous_to - timedelta(days=7)
    current_mid = now_from + ((now_to - now_from) / 2)
    previous_mid = previous_from + ((previous_to - previous_from) / 2)

    with Session() as db:
        for idx in range(current_count):
            db.add(
                OpsActionAudit(
                    id=f"cur_{idx:04d}",
                    action="PARTNER_STATUS_UPDATE",
                    result="SUCCESS",
                    correlation_id=f"corr_cur_{idx:04d}",
                    user_id="user_ops",
                    role="admin_operacao",
                    order_id=None,
                    error_message=None,
                    details_json={"partner_id": partner_id, "bucket": "current"},
                    created_at=current_mid,
                )
            )
        for idx in range(previous_count):
            db.add(
                OpsActionAudit(
                    id=f"prev_{idx:04d}",
                    action="PARTNER_STATUS_UPDATE",
                    result="SUCCESS",
                    correlation_id=f"corr_prev_{idx:04d}",
                    user_id="user_ops",
                    role="admin_operacao",
                    order_id=None,
                    error_message=None,
                    details_json={"partner_id": partner_id, "bucket": "previous"},
                    created_at=previous_mid,
                )
            )
        # Ruído de outro parceiro para validar o filtro partner_id.
        db.add(
            OpsActionAudit(
                id="noise_partner_0001",
                action="PARTNER_CONTACT_UPSERT",
                result="SUCCESS",
                correlation_id="corr_noise_0001",
                user_id="user_ops",
                role="admin_operacao",
                order_id=None,
                error_message=None,
                details_json={"partner_id": "partner_noise_999"},
                created_at=current_mid,
            )
        )
        db.commit()

    return now_from, now_to


@pytest.mark.parametrize(
    ("current_count", "previous_count", "expected_confidence", "expected_flag"),
    [
        (0, 0, "LOW", "NO_EVENTS_BOTH_WINDOWS"),
        (15, 20, "MEDIUM", "MEDIUM_VOLUME_BASELINE"),
        (35, 31, "HIGH", None),
    ],
)
def test_ops_audit_compare_confidence_and_data_quality_flags(
    monkeypatch,
    current_count,
    previous_count,
    expected_confidence,
    expected_flag,
):
    engine, Session, db_path = _prepare_db()
    try:
        client = _build_client(Session, monkeypatch)
        from_dt, to_dt = _seed_audit_rows(
            Session,
            current_count=current_count,
            previous_count=previous_count,
            partner_id="partner_focus_001",
        )

        response = client.get(
            "/partners/ops/audit/compare",
            params={
                "from": from_dt.isoformat(),
                "to": to_dt.isoformat(),
                "partner_id": "partner_focus_001",
            },
        )
        assert response.status_code == 200
        payload = response.json()

        assert payload["timezone_ref"] == "UTC"
        assert payload["confidence_level"] == expected_confidence
        assert payload["confidence_badge"]["key"] == f"confidence_{expected_confidence.lower()}"
        assert isinstance(payload["data_quality_flags"], list)

        if expected_flag is not None:
            assert expected_flag in payload["data_quality_flags"]
        else:
            assert "LOW_VOLUME_BASELINE" not in payload["data_quality_flags"]
            assert "MEDIUM_VOLUME_BASELINE" not in payload["data_quality_flags"]

        assert payload["total_current"] == current_count
        assert payload["total_previous"] == previous_count
    finally:
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass

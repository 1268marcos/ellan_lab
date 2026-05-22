from __future__ import annotations

from types import SimpleNamespace

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.services.promotion_scope_service import evaluate_promotion_scopes


def test_evaluate_scopes_include_country():
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE promotion_scopes (
                    promotion_id TEXT, scope_type TEXT, scope_value TEXT, mode TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                "INSERT INTO promotion_scopes VALUES ('p1', 'COUNTRY', 'BR', 'INCLUDE')"
            )
        )
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    ok, reason = evaluate_promotion_scopes(db, "p1", country_code="BR")
    assert ok is True
    assert reason == ""
    ok2, reason2 = evaluate_promotion_scopes(db, "p1", country_code="PT")
    assert ok2 is False
    assert "COUNTRY" in reason2
    db.close()


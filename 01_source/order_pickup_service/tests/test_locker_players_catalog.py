from __future__ import annotations

from app.core.locker_players_catalog import resolve_player_code
from app.data.catalog_players_registry import PLAYERS_REGISTRY
from app.services.promotion_scope_service import evaluate_promotion_scopes

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def test_catalog_includes_requested_players():
    codes = {p["code"] for p in PLAYERS_REGISTRY}
    for required in (
        "INPOST",
        "DHL_PACKSTATION",
        "MAGALU",
        "MERCADO_LIVRE",
        "AMAZON_HUB",
        "DPD",
        "CORREIOS",
        "CTT",
        "WORTEN",
        "EL_CORTE_INGLES",
    ):
        assert required in codes
    assert resolve_player_code("AMAZON") == "AMAZON_HUB"
    assert resolve_player_code("DHL") == "DHL_PACKSTATION"


def test_resolve_mercadolivre_alias():
    assert resolve_player_code("MercadoLivre") == "MERCADO_LIVRE"
    assert resolve_player_code("ML") == "MERCADO_LIVRE"


def test_scope_matches_player_alias():
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
                "INSERT INTO promotion_scopes VALUES ('p1', 'PLAYER', 'MERCADO_LIVRE', 'INCLUDE')"
            )
        )
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    ok, _ = evaluate_promotion_scopes(db, "p1", player_code="MERCADOLIVRE")
    assert ok is True
    db.close()

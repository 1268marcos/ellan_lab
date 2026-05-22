from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.promotions_players_integration import resolve_player_code_db as resolve_player_code

SCOPE_CONTEXT_FIELDS = {
    "COUNTRY": "country_code",
    "CHANNEL": "channel_code",
    "PARTNER": "partner_id",
    "PLAYER": "player_code",
    "REGION": "region_code",
    "TENANT": "tenant_id",
    "LOCKER_OPERATOR": "locker_operator_code",
    "MARKETPLACE": "marketplace_code",
}


def _norm(value: str | None) -> str:
    return str(value or "").strip().upper()


def _canonical_scope_value(db: Session, scope_type: str, scope_value: str) -> str:
    st = _norm(scope_type)
    if st in ("PLAYER", "MARKETPLACE", "LOCKER_OPERATOR"):
        return resolve_player_code(db, scope_value) or _norm(scope_value)
    return _norm(scope_value)


def _scope_matches(
    db: Session,
    scope_type: str,
    scope_value: str,
    context: dict[str, str | None],
) -> bool:
    field = SCOPE_CONTEXT_FIELDS.get(_norm(scope_type))
    if not field:
        return False
    ctx_raw = context.get(field)
    ctx_val = _canonical_scope_value(db, scope_type, str(ctx_raw or "")) if ctx_raw else ""
    target = _canonical_scope_value(db, scope_type, scope_value)
    if not ctx_val or not target:
        return False
    return ctx_val == target or target in ctx_val or ctx_val in target


def evaluate_promotion_scopes(
    db: Session,
    promotion_id: str,
    *,
    country_code: str | None = None,
    channel_code: str | None = None,
    player_code: str | None = None,
    partner_id: str | None = None,
    region_code: str | None = None,
    tenant_id: str | None = None,
    locker_operator_code: str | None = None,
    marketplace_code: str | None = None,
) -> tuple[bool, str]:
    rows = db.execute(
        text(
            """
            SELECT scope_type, scope_value, mode
            FROM promotion_scopes
            WHERE promotion_id = :pid
            """
        ),
        {"pid": promotion_id},
    ).mappings().all()
    if not rows:
        return True, ""

    context = {
        "country_code": country_code,
        "channel_code": channel_code,
        "player_code": player_code,
        "partner_id": partner_id,
        "region_code": region_code,
        "tenant_id": tenant_id,
        "locker_operator_code": locker_operator_code,
        "marketplace_code": marketplace_code,
    }

    for row in rows:
        if _norm(row.get("mode")) == "EXCLUDE" and _scope_matches(
            db,
            str(row.get("scope_type") or ""),
            str(row.get("scope_value") or ""),
            context,
        ):
            return False, f"excluído por escopo {row.get('scope_type')}={row.get('scope_value')}"

    includes = [r for r in rows if _norm(r.get("mode")) == "INCLUDE"]
    if not includes:
        return True, ""

    by_type: dict[str, list] = {}
    for row in includes:
        st = _norm(row.get("scope_type"))
        by_type.setdefault(st, []).append(row)

    for scope_type, group in by_type.items():
        if not any(
            _scope_matches(db, scope_type, str(r.get("scope_value") or ""), context) for r in group
        ):
            return False, f"fora do escopo {scope_type} da promoção"

    return True, ""

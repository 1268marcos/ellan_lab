from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.data.world_locker_payment_players import (
    PAYMENT_ECOSYSTEM_SEGMENTS,
    PAYMENT_PRIORITY_CODES,
    get_all_payment_players,
    get_payment_player_relations,
)
from app.data.world_locker_payment_players_extended import (
    build_country_coverage_rows,
    get_integration_profiles,
)
from app.models.cross_domain import (
    PaymentEcosystemPlayer,
    PaymentEcosystemSegment,
    PaymentPlayerCountryCoverage,
    PaymentPlayerIntegration,
    PaymentPlayerRelation,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _default_integration_for_player(code: str, segment: str, meta: dict) -> dict:
    profiles = get_integration_profiles()
    if code in profiles:
        p = profiles[code]
        return {
            "protocol": p.get("protocol", "REST"),
            "sandbox_ready": p.get("sandbox_ready", False),
            "production_ready": p.get("production_ready", False),
            "readiness_score": p.get("readiness_score", 40),
            "payment_capture_mode": p.get("capture", "CAPTURE_NOW"),
            "split_settlement_supported": p.get("split", False),
            "cross_border_supported": p.get("cross_border", False),
            "linked_domains_json": p.get("domains", ["order_pickup"]),
            "integration_notes": p.get("notes"),
        }
    score = 70 if code in PAYMENT_PRIORITY_CODES else 35
    if segment == "FOOD_DELIVERY":
        score = 45
    elif segment == "PAYMENTS_FISCAL":
        score = 75
    return {
        "protocol": "REST",
        "sandbox_ready": code in PAYMENT_PRIORITY_CODES,
        "production_ready": code in PAYMENT_PRIORITY_CODES,
        "readiness_score": score,
        "payment_capture_mode": "SPLIT_SETTLEMENT" if segment == "MARKETPLACE" else "CAPTURE_NOW",
        "split_settlement_supported": segment in ("MARKETPLACE", "LOGISTICS_PLATFORM"),
        "cross_border_supported": bool(meta.get("cambio_corridor_code")),
        "linked_domains_json": ["order_pickup", "payment_gateway"],
        "integration_notes": f"Integração padrão {segment} — revisar playbook OPS.",
    }


def upsert_ecosystem_catalog(db: Session) -> dict[str, int]:
    counts = {
        "players_created": 0,
        "players_updated": 0,
        "relations_created": 0,
        "segments": 0,
        "country_coverage": 0,
        "integrations": 0,
    }

    for seg in PAYMENT_ECOSYSTEM_SEGMENTS:
        if not db.get(PaymentEcosystemSegment, seg["code"]):
            db.add(
                PaymentEcosystemSegment(
                    code=seg["code"],
                    name=seg["name"],
                    description=seg.get("description"),
                    sort_order=10 * (PAYMENT_ECOSYSTEM_SEGMENTS.index(seg) + 1),
                    is_active=True,
                )
            )
            counts["segments"] += 1

    player_codes: set[str] = set()
    for pdata in get_all_payment_players():
        code = pdata["code"]
        player_codes.add(code)
        row = db.query(PaymentEcosystemPlayer).filter(PaymentEcosystemPlayer.code == code).first()
        if row:
            row.name = pdata["name"]
            row.segment = pdata["segment"]
            row.countries_json = pdata["countries_json"]
            row.parent_player_code = pdata.get("parent_player_code")
            row.integration_status = pdata["integration_status"]
            row.metadata_json = {**(row.metadata_json or {}), **pdata["metadata_json"]}
            row.is_active = True
            counts["players_updated"] += 1
        else:
            db.add(
                PaymentEcosystemPlayer(
                    id=f"pep-{code.lower()[:24]}",
                    code=code,
                    name=pdata["name"],
                    segment=pdata["segment"],
                    countries_json=pdata["countries_json"],
                    parent_player_code=pdata.get("parent_player_code"),
                    integration_status=pdata["integration_status"],
                    metadata_json=pdata["metadata_json"],
                    is_active=True,
                )
            )
            counts["players_created"] += 1

        integ = _default_integration_for_player(code, pdata["segment"], pdata["metadata_json"])
        irow = db.query(PaymentPlayerIntegration).filter(PaymentPlayerIntegration.player_code == code).first()
        if irow:
            irow.integration_protocol = integ["protocol"]
            irow.sandbox_ready = integ["sandbox_ready"]
            irow.production_ready = integ["production_ready"]
            irow.readiness_score = integ["readiness_score"]
            irow.payment_capture_mode = integ["payment_capture_mode"]
            irow.split_settlement_supported = integ["split_settlement_supported"]
            irow.cross_border_supported = integ["cross_border_supported"]
            irow.linked_domains_json = integ["linked_domains_json"]
            if integ.get("integration_notes"):
                irow.integration_notes = integ["integration_notes"]
            irow.updated_at = _utcnow()
        else:
            db.add(
                PaymentPlayerIntegration(
                    id=new_id(),
                    player_code=code,
                    integration_protocol=integ["protocol"],
                    sandbox_ready=integ["sandbox_ready"],
                    production_ready=integ["production_ready"],
                    readiness_score=integ["readiness_score"],
                    payment_capture_mode=integ["payment_capture_mode"],
                    split_settlement_supported=integ["split_settlement_supported"],
                    cross_border_supported=integ["cross_border_supported"],
                    linked_domains_json=integ["linked_domains_json"],
                    integration_notes=integ["integration_notes"],
                )
            )
            counts["integrations"] += 1

    for cov in build_country_coverage_rows():
        if cov["player_code"] not in player_codes:
            continue
        exists = (
            db.query(PaymentPlayerCountryCoverage)
            .filter(
                PaymentPlayerCountryCoverage.player_code == cov["player_code"],
                PaymentPlayerCountryCoverage.country_code == cov["country_code"],
                PaymentPlayerCountryCoverage.coverage_role == cov["coverage_role"],
            )
            .first()
        )
        if exists:
            continue
        db.add(
            PaymentPlayerCountryCoverage(
                id=new_id(),
                player_code=cov["player_code"],
                country_code=cov["country_code"],
                coverage_role=cov["coverage_role"],
                is_primary_market=cov["is_primary_market"],
                locker_density=cov["locker_density"],
            )
        )
        counts["country_coverage"] += 1

    for rel in get_payment_player_relations():
        exists = (
            db.query(PaymentPlayerRelation)
            .filter(
                PaymentPlayerRelation.from_player_code == rel["from"],
                PaymentPlayerRelation.to_player_code == rel["to"],
                PaymentPlayerRelation.relation_type == rel["type"],
            )
            .first()
        )
        if exists:
            continue
        if rel["from"] not in player_codes or rel["to"] not in player_codes:
            continue
        db.add(
            PaymentPlayerRelation(
                id=new_id(),
                from_player_code=rel["from"],
                to_player_code=rel["to"],
                relation_type=rel["type"],
                notes=rel.get("notes"),
                metadata_json={"source": "world_locker_payment_players"},
                is_active=True,
            )
        )
        counts["relations_created"] += 1
    db.commit()
    return counts

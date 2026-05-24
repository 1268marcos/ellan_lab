from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.data.locker_network_players_catalog import (
    LOCKER_NETWORK_PLAYERS_CATALOG,
    PRIORITY_LOCKER_CODES,
    global_tier_for_code,
    integration_status_for_entry,
)
from app.services import ecosystem_service
from app.models.ml_network import MlLockerNetworkPlayer, MlNetworkMlProfile
from app.models.ml_ops import MlUseCase
from app.models.partner import MlDataPartner
from app.services.crypto_util import new_id

NETWORK_USE_CASE_CODES = ("NETWORK_HEALTH_BENCHMARK", "CROSS_NETWORK_OCCUPANCY", "LOCKER_HEALTH")

DEFAULT_FEATURE_PACK = [
    "network_uptime_7d",
    "parcel_throughput_7d",
    "locker_fill_rate_7d",
    "door_failures_7d",
]

TELEMETRY_PARTNER_BY_NETWORK = {
    "INPOST": ("TELEMETRY-INPOST", "InPost Telemetria", "EU"),
    "DHL": ("TELEMETRY-DHL", "DHL Telemetria", "EU"),
    "DPD": ("TELEMETRY-DPD", "DPD Telemetria", "EU"),
    "CTT": ("TELEMETRY-CTT", "CTT Telemetria", "PT"),
    "CORREIOS": ("TELEMETRY-CORREIOS", "Correios Telemetria", "BR"),
    "MAGALU": ("TELEMETRY-MAGALU", "Magalu Telemetria", "BR"),
    "MERCADOLIVRE": ("TELEMETRY-MELI", "Mercado Livre Telemetria", "BR"),
    "AMAZON_BR": ("TELEMETRY-AMAZON-BR", "Amazon BR Telemetria", "BR"),
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _row_to_player_out(row: MlLockerNetworkPlayer) -> dict:
    regions = row.regions_json
    try:
        regions_list = json.loads(regions) if isinstance(regions, str) else list(regions or [])
    except json.JSONDecodeError:
        regions_list = []
    return {
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "player_role": row.player_role,
        "parent_group": row.parent_group,
        "country": row.country,
        "regions": regions_list,
        "supports_lockers": row.supports_lockers,
        "supports_marketplace": row.supports_marketplace,
        "integration_mode": row.integration_mode,
        "marketplace_channel_id": row.marketplace_channel_id,
        "marketplace_channel_code": row.marketplace_channel_code,
        "locker_operator_ref": row.locker_operator_ref,
        "ecommerce_partner_code": row.ecommerce_partner_code,
        "api_docs_url": row.api_docs_url,
        "ml_scoring_weight": float(row.ml_scoring_weight or 1),
        "ml_notes": row.ml_notes,
        "global_tier": getattr(row, "global_tier", None) or "REGIONAL",
        "integration_status": getattr(row, "integration_status", None) or "PLANNED",
        "data_source": getattr(row, "data_source", None) or "CATALOG",
        "finance_catalog_code": getattr(row, "finance_catalog_code", None) or row.code,
        "sort_order": row.sort_order,
        "active": row.active,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def list_network_players(
    db: Session,
    *,
    active_only: bool = False,
    parent_group: str | None = None,
    country: str | None = None,
    priority_only: bool = False,
) -> list[MlLockerNetworkPlayer]:
    q = db.query(MlLockerNetworkPlayer)
    if active_only:
        q = q.filter(MlLockerNetworkPlayer.active.is_(True))
    if parent_group:
        q = q.filter(MlLockerNetworkPlayer.parent_group == parent_group)
    if country:
        q = q.filter(MlLockerNetworkPlayer.country == country.upper())
    if priority_only:
        q = q.filter(MlLockerNetworkPlayer.code.in_(PRIORITY_LOCKER_CODES))
    return q.order_by(MlLockerNetworkPlayer.sort_order, MlLockerNetworkPlayer.code).all()


def get_network_player_by_finance_code(db: Session, finance_catalog_code: str) -> dict | None:
    code = finance_catalog_code.upper()
    row = (
        db.query(MlLockerNetworkPlayer)
        .filter(
            (MlLockerNetworkPlayer.finance_catalog_code == code) | (MlLockerNetworkPlayer.code == code)
        )
        .first()
    )
    return _row_to_player_out(row) if row else None


def list_network_profiles(db: Session, network_player_id: str | None = None) -> list[dict]:
    q = db.query(MlNetworkMlProfile, MlLockerNetworkPlayer, MlUseCase).join(
        MlLockerNetworkPlayer, MlNetworkMlProfile.network_player_id == MlLockerNetworkPlayer.id
    ).outerjoin(MlUseCase, MlNetworkMlProfile.use_case_id == MlUseCase.id)
    if network_player_id:
        q = q.filter(MlNetworkMlProfile.network_player_id == network_player_id)
    rows = q.order_by(MlLockerNetworkPlayer.code).all()
    out: list[dict] = []
    for prof, net, uc in rows:
        try:
            pack = json.loads(prof.feature_pack_json) if prof.feature_pack_json else []
        except json.JSONDecodeError:
            pack = []
        out.append(
            {
                "id": prof.id,
                "network_player_id": prof.network_player_id,
                "network_player_code": net.code,
                "use_case_id": prof.use_case_id,
                "use_case_code": uc.code if uc else None,
                "telemetry_density": prof.telemetry_density,
                "drift_baseline_psi": float(prof.drift_baseline_psi) if prof.drift_baseline_psi is not None else None,
                "feature_pack": pack,
                "active": prof.active,
                "created_at": prof.created_at,
            }
        )
    return out


def seed_from_catalog(db: Session) -> dict[str, int]:
    inserted = updated = profiles_created = partners_linked = 0
    use_cases = {
        uc.code: uc
        for uc in db.query(MlUseCase).filter(MlUseCase.code.in_(NETWORK_USE_CASE_CODES)).all()
    }

    for entry in LOCKER_NETWORK_PLAYERS_CATALOG:
        code = entry["code"]
        row = db.query(MlLockerNetworkPlayer).filter(MlLockerNetworkPlayer.code == code).first()
        payload = {
            "name": entry["name"],
            "player_role": entry["player_role"],
            "parent_group": entry["parent_group"],
            "country": entry["country"],
            "regions_json": entry.get("regions_json") or "[]",
            "supports_lockers": entry.get("supports_lockers", True),
            "supports_marketplace": entry.get("supports_marketplace", False),
            "integration_mode": entry.get("integration_mode") or "DIRECT_API",
            "marketplace_channel_id": entry.get("marketplace_channel_id"),
            "marketplace_channel_code": entry.get("marketplace_channel_code"),
            "locker_operator_ref": entry.get("locker_operator_ref"),
            "ecommerce_partner_code": entry.get("ecommerce_partner_code"),
            "api_docs_url": entry.get("api_docs_url"),
            "ml_scoring_weight": entry.get("ml_scoring_weight", 1.0),
            "ml_notes": entry.get("ml_notes"),
            "global_tier": global_tier_for_code(code),
            "integration_status": integration_status_for_entry(entry),
            "data_source": "MARKETPLACE_CATALOG" if entry.get("marketplace_channel_id") else "CATALOG",
            "finance_catalog_code": entry.get("finance_catalog_code") or code,
            "sort_order": entry.get("sort_order", 100),
            "active": True,
            "updated_at": _utcnow(),
        }
        if not row:
            row = MlLockerNetworkPlayer(id=entry.get("marketplace_channel_id") or new_id(), code=code, **payload)
            db.add(row)
            inserted += 1
        else:
            for k, v in payload.items():
                setattr(row, k, v)
            updated += 1
        db.flush()

        benchmark_uc = use_cases.get("NETWORK_HEALTH_BENCHMARK") or use_cases.get("LOCKER_HEALTH")
        if benchmark_uc and not db.query(MlNetworkMlProfile).filter(
            MlNetworkMlProfile.network_player_id == row.id,
            MlNetworkMlProfile.use_case_id == benchmark_uc.id,
        ).first():
            density = "HIGH" if code in PRIORITY_LOCKER_CODES else "MEDIUM"
            db.add(
                MlNetworkMlProfile(
                    id=new_id(),
                    network_player_id=row.id,
                    use_case_id=benchmark_uc.id,
                    telemetry_density=density,
                    drift_baseline_psi=0.10 if code in PRIORITY_LOCKER_CODES else 0.15,
                    feature_pack_json=json.dumps(DEFAULT_FEATURE_PACK),
                    active=True,
                )
            )
            profiles_created += 1

        tpl = TELEMETRY_PARTNER_BY_NETWORK.get(code)
        if tpl:
            p_code, p_name, region = tpl
            partner = db.query(MlDataPartner).filter(MlDataPartner.code == p_code).first()
            if not partner:
                partner = MlDataPartner(
                    id=new_id(),
                    name=p_name,
                    code=p_code,
                    partner_type="TELEMETRY",
                    region_code=region,
                    api_base_url=f"https://telemetry.example/{code.lower()}",
                    active=True,
                )
                db.add(partner)
                partners_linked += 1
            if hasattr(MlDataPartner, "network_player_code"):
                if getattr(partner, "network_player_code", None) != code:
                    partner.network_player_code = code
                    partners_linked += 1

    eco = ecosystem_service.seed_player_ecosystem(db, LOCKER_NETWORK_PLAYERS_CATALOG)
    from app.services import readiness_service

    readiness_service.recompute_ml_readiness(db)
    db.commit()
    return {
        "inserted": inserted,
        "updated": updated,
        "profiles_created": profiles_created,
        "partners_linked": partners_linked,
        "catalog_size": len(LOCKER_NETWORK_PLAYERS_CATALOG),
        **eco,
    }


def network_dashboard_counts(db: Session) -> dict:
    total = db.query(MlLockerNetworkPlayer).count()
    active = db.query(MlLockerNetworkPlayer).filter(MlLockerNetworkPlayer.active.is_(True)).count()
    priority = (
        db.query(MlLockerNetworkPlayer)
        .filter(
            MlLockerNetworkPlayer.active.is_(True),
            MlLockerNetworkPlayer.code.in_(PRIORITY_LOCKER_CODES),
        )
        .count()
    )
    profiles = db.query(MlNetworkMlProfile).filter(MlNetworkMlProfile.active.is_(True)).count()
    locker_ops = (
        db.query(MlLockerNetworkPlayer)
        .filter(MlLockerNetworkPlayer.parent_group == "LOCKER_NETWORK", MlLockerNetworkPlayer.active.is_(True))
        .count()
    )
    eco = ecosystem_service.ecosystem_counts(db)
    return {
        "locker_network_players": total,
        "locker_network_active": active,
        "locker_network_priority": priority,
        "network_ml_profiles": profiles,
        "locker_operators": locker_ops,
        **eco,
    }


def get_network_or_404(db: Session, player_id: str) -> MlLockerNetworkPlayer:
    row = db.get(MlLockerNetworkPlayer, player_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="network_player_not_found")
    return row

from __future__ import annotations

import time
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.data.global_locker_players_catalog import (
    GLOBAL_CARRIERS,
    GLOBAL_CHANNEL_BINDINGS,
    GLOBAL_DOMAIN_REFS,
    GLOBAL_LOCKER_PLAYERS,
    GLOBAL_MARKETPLACE_LINKS,
    GLOBAL_OPERATORS,
    GLOBAL_RUNTIME_LOCKERS,
    PLAYER_SEGMENTS,
)
from app.models.assets import HardwareAsset
from app.models.cross_domain import (
    HardwareDomainReference,
    HardwareEcosystemPlayer,
    HardwareLockerCarrierBinding,
    HardwareLockerMarketplaceLink,
    HardwareLockerPaymentBinding,
)
from app.models.finance import HardwareLockerCapex, HardwareLockerOpex
from app.models.hardware_ops import HardwareSyncQueue, HardwareTelemetryEvent
from app.models.integration import HardwareLockerChannelBinding
from app.models.operators import LockerOperator
from app.models.runtime import HardwareDeviceRegistry, RuntimeLocker
from app.models.topology import HardwareLockerFeature, HardwareLockerSlot
from app.models.vendor import HardwareVendorPartner
from app.services.crypto_util import new_id
from app.services import integration_service, professional_ops_service

VENDORS = [
    ("hw-v-swipebox", "SwipBox", "SWIPBOX", "LOCKER_NETWORK", "EU"),
    ("hw-v-cleveron", "Cleveron", "CLEVERON", "LOCKER_NETWORK", "EU"),
    ("hw-v-pickup-pl", "Pickup (PL)", "PICKUP-PL", "LOCKER_NETWORK", "PL"),
    ("hw-v-bloqit", "Bloq.it", "BLOQIT", "LOCKER_NETWORK", "EU"),
    ("hw-v-quadient", "Quadient", "QUADIENT", "LOCKER_NETWORK", "EU"),
    ("hw-v-packeta", "Packeta", "PACKETA", "LOCKER_NETWORK", "CZ"),
    ("hw-v-vintedgo", "Vinted Go", "VINTEDGO", "LOCKER_NETWORK", "EU"),
]

DEMO_LOCKER = "LOCKER-DEMO-01"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _vendor_country(region: str) -> str:
    if region == "EU":
        return "DE"
    return region


def seed_ecosystem_players(db: Session) -> int:
    integration_service.seed_segments(db, PLAYER_SEGMENTS)
    count = 0
    for player in GLOBAL_LOCKER_PLAYERS:
        pid = player["id"]
        if db.get(HardwareEcosystemPlayer, pid):
            continue
        db.add(
            HardwareEcosystemPlayer(
                id=pid,
                player_code=player["player_code"],
                name=player["name"],
                segment=player["segment"],
                parent_group=player["parent_group"],
                integration_mode=player["integration_mode"],
                supports_lockers=player["supports_lockers"],
                supports_marketplace=player["supports_marketplace"],
                supports_food_delivery=player["supports_food_delivery"],
                supports_aggregation=player["supports_aggregation"],
                primary_country=player["primary_country"],
                vendor_id=player.get("vendor_id"),
                operator_id=player.get("operator_id"),
                marketplace_channel_code=player.get("marketplace_channel_code"),
                ml_network_code=player.get("ml_network_code"),
                payment_provider_code=player.get("payment_provider_code"),
                finance_catalog_code=player.get("finance_catalog_code"),
                fiscal_corridor_code=player.get("fiscal_corridor_code"),
                carrier_code=player.get("carrier_code"),
                regions_json=player["regions_json"],
                metadata_json={"catalog": "global_locker_players", "seed": True},
            )
        )
        count += 1
    if count:
        db.commit()
    integration_service.seed_player_capabilities_and_relations(db, GLOBAL_LOCKER_PLAYERS)
    return count


def run_seed(db: Session) -> dict[str, int]:
    counts = {
        "vendors": 0,
        "operators": 0,
        "runtime_lockers": 0,
        "assets": 0,
        "devices": 0,
        "sync_queue": 0,
        "telemetry": 0,
        "ecosystem_players": 0,
        "marketplace_links": 0,
        "payment_bindings": 0,
        "carrier_bindings": 0,
        "domain_references": 0,
        "capex": 0,
        "opex": 0,
        "locker_features": 0,
        "locker_slots": 0,
        "segments": 0,
        "capabilities": 0,
        "player_relations": 0,
        "channel_bindings": 0,
        "playbooks": 0,
        "certifications": 0,
        "corridors": 0,
        "incidents": 0,
        "webhooks": 0,
        "onboarding_runs": 0,
    }
    now = _utcnow()
    epoch = int(time.time())

    for vid, name, code, vtype, region in VENDORS:
        if db.get(HardwareVendorPartner, vid):
            continue
        db.add(
            HardwareVendorPartner(
                id=vid,
                name=name,
                code=code,
                vendor_type=vtype,
                region_code=region,
                api_base_url=f"https://api.{code.lower()}.example/v1",
                country=_vendor_country(region),
                active=True,
            )
        )
        counts["vendors"] += 1

    for oid, name, otype, country in GLOBAL_OPERATORS:
        if db.get(LockerOperator, oid):
            continue
        db.add(
            LockerOperator(
                id=oid,
                name=name,
                operator_type=otype,
                country=country,
                active=True,
                status="ACTIVE",
                tier="PREMIUM",
                created_at=now,
                updated_at=now,
            )
        )
        counts["operators"] += 1

    if not db.get(RuntimeLocker, DEMO_LOCKER):
        db.add(
            RuntimeLocker(
                locker_id=DEMO_LOCKER,
                machine_id="MACHINE-DEMO-01",
                display_name="Locker Demo São Paulo",
                region="BR-SP",
                country="BR",
                timezone="America/Sao_Paulo",
                operator_id="op-meli",
                vendor_id="hw-v-swipebox",
                mqtt_region="br",
                mqtt_locker_id="demo-01",
                slot_count_total=24,
                payment_methods_json=["PIX", "CREDIT_CARD"],
            )
        )
        counts["runtime_lockers"] += 1

    if not db.query(HardwareAsset).filter(HardwareAsset.asset_code == "EHA-DEMO-LOCKER-01").first():
        asset_id = new_id()
        db.add(
            HardwareAsset(
                id=asset_id,
                asset_code="EHA-DEMO-LOCKER-01",
                locker_id=DEMO_LOCKER,
                vendor_id="hw-v-swipebox",
                asset_category="LOCKER",
                description="Armário principal demo — SwipBox 24 slots",
                acquisition_date=date(2024, 6, 1),
                in_service_date=date(2024, 7, 1),
                acquisition_cost_cents=4500000,
                installation_cost_cents=350000,
                useful_life_months=60,
                supplier_name="SwipBox A/S",
                status="ACTIVE",
                metadata_json={"slots": 24, "has_kiosk": True, "has_ble": True},
            )
        )
        counts["assets"] += 1
    else:
        asset_id = db.query(HardwareAsset).filter(HardwareAsset.asset_code == "EHA-DEMO-LOCKER-01").first().id

    device_hash = "hw-demo-device-001"
    if not db.get(HardwareDeviceRegistry, device_hash):
        db.add(
            HardwareDeviceRegistry(
                device_hash=device_hash,
                version="1.2.0",
                first_seen_at_epoch=epoch - 86400,
                last_seen_at_epoch=epoch,
                seen_count=42,
                locker_id=DEMO_LOCKER,
                vendor_id="hw-v-swipebox",
                region_code="BR-SP",
                flags_json={"has_nfc": True, "has_printer": False},
            )
        )
        counts["devices"] += 1

    if not db.query(HardwareSyncQueue).filter(HardwareSyncQueue.locker_id == DEMO_LOCKER).first():
        db.add(
            HardwareSyncQueue(
                id=new_id(),
                locker_id=DEMO_LOCKER,
                operation="SLOT_TOPOLOGY_SYNC",
                status="PENDING",
                retry_count=0,
            )
        )
        counts["sync_queue"] += 1

    if not db.query(HardwareTelemetryEvent).filter(HardwareTelemetryEvent.locker_id == DEMO_LOCKER).first():
        db.add(
            HardwareTelemetryEvent(
                id=new_id(),
                locker_id=DEMO_LOCKER,
                event_type="HEARTBEAT",
                severity="INFO",
                payload_json={"uptime_sec": 86400, "temp_c": 28.5},
                created_at_epoch=epoch,
            )
        )
        db.add(
            HardwareTelemetryEvent(
                id=new_id(),
                locker_id=DEMO_LOCKER,
                event_type="DOOR_OPEN",
                severity="INFO",
                slot_number=3,
                payload_json={"duration_ms": 4200},
                created_at_epoch=epoch - 120,
            )
        )
        counts["telemetry"] += 2

    counts["ecosystem_players"] = seed_ecosystem_players(db)

    player_code_to_id = {p.player_code: p.id for p in db.query(HardwareEcosystemPlayer).all()}
    for locker_id, channel_type, player_code, player_name, integration_mode, priority in GLOBAL_CHANNEL_BINDINGS:
        exists = (
            db.query(HardwareLockerChannelBinding)
            .filter(
                HardwareLockerChannelBinding.locker_id == locker_id,
                HardwareLockerChannelBinding.channel_type == channel_type,
                HardwareLockerChannelBinding.player_code == player_code,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            HardwareLockerChannelBinding(
                id=new_id(),
                locker_id=locker_id,
                channel_type=channel_type,
                player_id=player_code_to_id.get(player_code),
                player_code=player_code,
                player_name=player_name,
                integration_mode=integration_mode,
                priority=priority,
            )
        )
        counts["channel_bindings"] += 1

    for seller_id, seller_name, channel_id, channel_code, channel_name, priority in GLOBAL_MARKETPLACE_LINKS:
        exists = (
            db.query(HardwareLockerMarketplaceLink)
            .filter(
                HardwareLockerMarketplaceLink.seller_id == seller_id,
                HardwareLockerMarketplaceLink.channel_code == channel_code,
                HardwareLockerMarketplaceLink.locker_id == DEMO_LOCKER,
            )
            .first()
        )
        if exists:
            continue
        vendor_id = "hw-v-swipebox" if channel_code in {"MAGALU", "AMAZON_BR", "MERCADOLIVRE"} else None
        db.add(
            HardwareLockerMarketplaceLink(
                id=new_id(),
                seller_id=seller_id,
                seller_name=seller_name,
                channel_partner_id=channel_id,
                channel_code=channel_code,
                channel_name=channel_name,
                locker_id=DEMO_LOCKER,
                vendor_id=vendor_id,
                priority=priority,
            )
        )
        counts["marketplace_links"] += 1

    for method, psp, iface in [("PIX", "MERCADOPAGO", "TOTEM_TOUCH"), ("CREDIT_CARD", "STRIPE", "TOTEM_TOUCH")]:
        exists = (
            db.query(HardwareLockerPaymentBinding)
            .filter(
                HardwareLockerPaymentBinding.locker_id == DEMO_LOCKER,
                HardwareLockerPaymentBinding.payment_method_code == method,
            )
            .first()
        )
        if not exists:
            db.add(
                HardwareLockerPaymentBinding(
                    id=new_id(),
                    locker_id=DEMO_LOCKER,
                    payment_method_code=method,
                    payment_provider_code=psp,
                    payment_interface_code=iface,
                    priority=100 if method == "PIX" else 90,
                )
            )
            counts["payment_bindings"] += 1

    demo_carriers = {"CORREIOS", "INPOST", "DHL", "DPD", "CTT"}
    for carrier_code, carrier_name, country, operator_id in GLOBAL_CARRIERS:
        if carrier_code not in demo_carriers:
            continue
        exists = (
            db.query(HardwareLockerCarrierBinding)
            .filter(
                HardwareLockerCarrierBinding.locker_id == DEMO_LOCKER,
                HardwareLockerCarrierBinding.carrier_code == carrier_code,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            HardwareLockerCarrierBinding(
                id=new_id(),
                locker_id=DEMO_LOCKER,
                carrier_code=carrier_code,
                carrier_name=carrier_name,
                country_code=country,
                operator_id=operator_id,
                tracking_prefix=carrier_code[:3],
            )
        )
        counts["carrier_bindings"] += 1

    for domain_type, external_id, external_code in GLOBAL_DOMAIN_REFS:
        exists = (
            db.query(HardwareDomainReference)
            .filter(
                HardwareDomainReference.locker_id == DEMO_LOCKER,
                HardwareDomainReference.domain_type == domain_type,
                HardwareDomainReference.external_id == external_id,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            HardwareDomainReference(
                id=new_id(),
                locker_id=DEMO_LOCKER,
                domain_type=domain_type,
                external_id=external_id,
                external_code=external_code,
                relation_type="PRIMARY" if domain_type == "ORDER_PICKUP" else "LINK",
            )
        )
        counts["domain_references"] += 1

    if not db.query(HardwareDomainReference).filter(
        HardwareDomainReference.locker_id == DEMO_LOCKER,
        HardwareDomainReference.domain_type == "FINANCE",
        HardwareDomainReference.external_id == asset_id,
    ).first():
        db.add(
            HardwareDomainReference(
                id=new_id(),
                locker_id=DEMO_LOCKER,
                domain_type="FINANCE",
                external_id=asset_id,
                external_code="CAPEX-ASSET",
                relation_type="LINK",
            )
        )
        counts["domain_references"] += 1

    if not db.query(HardwareLockerCapex).filter(HardwareLockerCapex.locker_id == DEMO_LOCKER).first():
        db.add(
            HardwareLockerCapex(
                id=new_id(),
                locker_id=DEMO_LOCKER,
                asset_id=asset_id,
                acquisition_cost_cents=4500000,
                installation_cost_cents=350000,
                equipment_cost_cents=3800000,
                connectivity_setup_cents=350000,
                depreciation_start_date=date(2024, 7, 1),
                supplier="SwipBox A/S",
            )
        )
        counts["capex"] += 1

    if not db.query(HardwareLockerOpex).filter(HardwareLockerOpex.locker_id == DEMO_LOCKER).first():
        db.add(
            HardwareLockerOpex(
                id=new_id(),
                locker_id=DEMO_LOCKER,
                reference_month=date(2025, 4, 1),
                cost_type="CONNECTIVITY",
                amount_cents=89000,
                description="Link 4G + backup fibra",
            )
        )
        db.add(
            HardwareLockerOpex(
                id=new_id(),
                locker_id=DEMO_LOCKER,
                reference_month=date(2025, 4, 1),
                cost_type="ENERGY",
                amount_cents=42000,
                description="Energia elétrica site",
            )
        )
        counts["opex"] += 2

    if not db.get(HardwareLockerFeature, DEMO_LOCKER):
        db.add(
            HardwareLockerFeature(
                locker_id=DEMO_LOCKER,
                supports_kiosk=True,
                supports_ble=True,
                supports_nfc=True,
                supports_printer=False,
                supports_card_reader=True,
            )
        )
        counts["locker_features"] += 1

    if not db.query(HardwareLockerSlot).filter(HardwareLockerSlot.locker_id == DEMO_LOCKER).first():
        for slot_num, size in [(1, "S"), (2, "M"), (3, "L"), (4, "XL")]:
            db.add(
                HardwareLockerSlot(
                    id=new_id(),
                    locker_id=DEMO_LOCKER,
                    slot_number=slot_num,
                    slot_size=size,
                    width_mm=400 if size == "S" else 600,
                    height_mm=300,
                    depth_mm=450,
                    max_weight_g=15000,
                )
            )
            counts["locker_slots"] += 1

    hub = integration_service.get_integration_hub_summary(db)
    counts["segments"] = hub.segments
    counts["capabilities"] = hub.capabilities
    counts["player_relations"] = hub.player_relations

    pro = professional_ops_service.seed_professional_ops(db)
    for k, v in pro.items():
        counts[k] = counts.get(k, 0) + v

    db.commit()
    return counts


def seed_network_runtime_lockers(db: Session) -> int:
    count = 0
    for (
        locker_id,
        machine_id,
        display_name,
        region,
        country,
        timezone,
        operator_id,
        vendor_id,
        mqtt_region,
        mqtt_locker_id,
        slot_count,
    ) in GLOBAL_RUNTIME_LOCKERS:
        if db.get(RuntimeLocker, locker_id):
            continue
        db.add(
            RuntimeLocker(
                locker_id=locker_id,
                machine_id=machine_id,
                display_name=display_name,
                region=region,
                country=country,
                timezone=timezone,
                operator_id=operator_id,
                vendor_id=vendor_id,
                mqtt_region=mqtt_region,
                mqtt_locker_id=mqtt_locker_id,
                slot_count_total=slot_count,
                payment_methods_json=["PIX", "CREDIT_CARD"] if country == "BR" else ["CREDIT_CARD"],
            )
        )
        count += 1
    if count:
        db.commit()
    return count


def seed_player_domain_references(db: Session) -> int:
    """Refs ML / FINANCE / FISCAL / MARKETPLACE por player do catálogo mundial."""
    count = 0
    locker_ids = [row[0] for row in GLOBAL_RUNTIME_LOCKERS]

    for player in GLOBAL_LOCKER_PLAYERS:
        target_locker = DEMO_LOCKER
        pcode = player["player_code"]
        for lid in locker_ids:
            if pcode.replace("-", "").upper() in lid.replace("-", "").upper():
                target_locker = lid
                break

        ref_specs: list[tuple[str, str, str]] = []
        if player.get("ml_network_code"):
            ref_specs.append(("ML", player["ml_network_code"], player["ml_network_code"]))
        if player.get("finance_catalog_code"):
            ref_specs.append(("FINANCE", player["finance_catalog_code"], player["finance_catalog_code"]))
        if player.get("fiscal_corridor_code"):
            ref_specs.append(("FISCAL", player["fiscal_corridor_code"], player["fiscal_corridor_code"]))
        if player.get("marketplace_channel_code"):
            ref_specs.append(
                ("MARKETPLACE", player["marketplace_channel_code"], player["marketplace_channel_code"])
            )
        if player.get("payment_provider_code"):
            ref_specs.append(
                ("PAYMENT_GATEWAY", player["payment_provider_code"], player["payment_provider_code"])
            )

        for domain_type, external_id, external_code in ref_specs:
            exists = (
                db.query(HardwareDomainReference)
                .filter(
                    HardwareDomainReference.locker_id == target_locker,
                    HardwareDomainReference.domain_type == domain_type,
                    HardwareDomainReference.external_id == external_id,
                )
                .first()
            )
            if exists:
                continue
            db.add(
                HardwareDomainReference(
                    id=new_id(),
                    locker_id=target_locker,
                    domain_type=domain_type,
                    external_id=external_id,
                    external_code=external_code,
                    relation_type="PLAYER_CATALOG",
                    notes=f"auto-seed player {pcode}",
                    metadata_json={"player_code": pcode, "seed": "domain_full"},
                )
            )
            count += 1

    if count:
        db.commit()
    return count


def seed_all_carrier_bindings(db: Session) -> int:
    count = 0
    for locker_id in {row[0] for row in GLOBAL_RUNTIME_LOCKERS}:
        for carrier_code, carrier_name, country, operator_id in GLOBAL_CARRIERS:
            exists = (
                db.query(HardwareLockerCarrierBinding)
                .filter(
                    HardwareLockerCarrierBinding.locker_id == locker_id,
                    HardwareLockerCarrierBinding.carrier_code == carrier_code,
                )
                .first()
            )
            if exists:
                continue
            db.add(
                HardwareLockerCarrierBinding(
                    id=new_id(),
                    locker_id=locker_id,
                    carrier_code=carrier_code,
                    carrier_name=carrier_name,
                    country_code=country,
                    operator_id=operator_id,
                    tracking_prefix=carrier_code[:3],
                    is_active=country in {"BR", "PL", "DE", "GB", "PT", "ES", "US"},
                )
            )
            count += 1
    if count:
        db.commit()
    return count


def run_domain_full_seed(db: Session, *, mirror_external: bool = False) -> dict[str, int]:
    """Seed completo do domínio Hardware — todos os players + redes + refs cross-domain."""
    counts = run_seed(db)
    counts["network_runtime_lockers"] = seed_network_runtime_lockers(db)
    counts["player_domain_refs"] = seed_player_domain_references(db)
    counts["all_carrier_bindings"] = seed_all_carrier_bindings(db)
    counts["ecosystem_players_total"] = db.query(HardwareEcosystemPlayer).count()

    if mirror_external:
        try:
            mirror_stats = integration_service.mirror_marketplace_channel_partners(db)
            counts["marketplace_channel_mirror"] = mirror_stats.get("matched", 0)
            counts["marketplace_links_mirrored"] = mirror_stats.get("links_created", 0)
        except Exception:
            counts["marketplace_channel_mirror"] = 0

    return counts

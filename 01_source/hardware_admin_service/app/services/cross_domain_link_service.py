from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.clients.domain_http import DomainHttpError, fetch_items, fetch_json
from app.core.config import get_settings
from app.models.cross_domain import (
    HardwareDomainReference,
    HardwareEcosystemPlayer,
    HardwareLockerCarrierBinding,
    HardwareLockerMarketplaceLink,
    HardwareLockerPaymentBinding,
)
from app.models.integration import HardwareLockerChannelBinding
from app.models.runtime import RuntimeLocker
from app.schemas.cross_domain_links import (
    CrossDomainGapItemOut,
    CrossDomainGapsScanOut,
    DomainReachabilityOut,
    DomainReferenceVerificationOut,
    EcosystemAlignmentItemOut,
    EcosystemAlignmentOut,
    Locker360Out,
    Locker360RemoteOut,
    PaymentBindingSyncOut,
)
from app.services.crypto_util import new_id


def _settings():
    return get_settings()


def _collect_locker_ids(db: Session) -> list[str]:
    ids: set[str] = set()
    for row in db.query(RuntimeLocker.locker_id).all():
        if row[0]:
            ids.add(row[0])
    for row in db.query(HardwareLockerPaymentBinding.locker_id).distinct().all():
        ids.add(row[0])
    for row in db.query(HardwareLockerMarketplaceLink.locker_id).filter(
        HardwareLockerMarketplaceLink.locker_id.isnot(None)
    ).all():
        if row[0]:
            ids.add(row[0])
    for row in db.query(HardwareDomainReference.locker_id).distinct().all():
        ids.add(row[0])
    return sorted(ids)


def probe_domain_reachability() -> list[DomainReachabilityOut]:
    s = _settings()
    probes = [
        ("PAYMENT_GATEWAY", f"{s.payment_gateway_admin_url}/api/v1/payment-gateway-admin/health"),
        ("ORDER_PICKUP", f"{s.order_pickup_admin_url}/api/v1/order-pickup-admin/health"),
        ("PAYMENTS", f"{s.payments_admin_url}/api/v1/payments-admin/health"),
        ("FINANCE", f"{s.finance_admin_url}/api/v1/finance-admin/health"),
        ("PARTNER", f"{s.partner_admin_url}/api/v1/partner-admin/health"),
        ("MARKETPLACE", f"{s.marketplace_admin_url}/api/v1/marketplace-admin/health"),
        ("FISCAL", f"{s.fiscal_admin_url}/api/v1/fiscal-admin/health"),
        ("ML", f"{s.ml_admin_url}/api/v1/ml-admin/health"),
    ]
    out: list[DomainReachabilityOut] = []
    for domain, url in probes:
        try:
            fetch_json(domain, url)
            out.append(DomainReachabilityOut(domain=domain, reachable=True))
        except DomainHttpError as exc:
            out.append(DomainReachabilityOut(domain=domain, reachable=False, detail=exc.detail))
    return out


def _fetch_fiscal_corridor(corridor_code: str) -> dict[str, Any] | None:
    if not corridor_code:
        return None
    s = _settings()
    url = f"{s.fiscal_admin_url}/api/v1/fiscal-admin/fiscal-global-ops/corridors/{corridor_code}"
    try:
        result = fetch_json("FISCAL", url)
        return result if isinstance(result, dict) else None
    except DomainHttpError:
        return None


def _fetch_fiscal_certifications(issuer_code: str | None = None) -> list[dict[str, Any]]:
    s = _settings()
    url = f"{s.fiscal_admin_url}/api/v1/fiscal-admin/fiscal-global-ops/certifications"
    params = {"issuer_id": issuer_code} if issuer_code else None
    return fetch_items("FISCAL", url, params=params)


def _fetch_ml_players(code: str | None = None) -> list[dict[str, Any]]:
    s = _settings()
    if code:
        url = f"{s.ml_admin_url}/api/v1/ml-admin/ml-locker-network-players/by-finance-code/{code}"
        try:
            result = fetch_json("ML", url)
            return [result] if isinstance(result, dict) else []
        except DomainHttpError:
            pass
    url = f"{s.ml_admin_url}/api/v1/ml-admin/ml-locker-network-players"
    return fetch_items("ML", url, params={"limit": 500})


def _fetch_marketplace_channel_partners() -> list[dict[str, Any]]:
    s = _settings()
    url = f"{s.marketplace_admin_url}/api/v1/marketplace-admin/channel-partners"
    return fetch_items("MARKETPLACE", url)


def _fetch_gateway_methods(locker_id: str | None = None) -> list[dict[str, Any]]:
    s = _settings()
    url = f"{s.payment_gateway_admin_url}/api/v1/payment-gateway-admin/locker-payment-methods"
    params = {"locker_id": locker_id} if locker_id else None
    return fetch_items("PAYMENT_GATEWAY", url, params=params)


def _fetch_pickups_for_locker(locker_id: str, limit: int = 100) -> list[dict[str, Any]]:
    s = _settings()
    url = f"{s.order_pickup_admin_url}/api/v1/order-pickup-admin/pickups"
    items = fetch_items("ORDER_PICKUP", url, params={"limit": limit})
    return [p for p in items if str(p.get("locker_id") or "") == locker_id]


def _fetch_payment_contexts(locker_id: str, limit: int = 50) -> list[dict[str, Any]]:
    s = _settings()
    url = f"{s.payments_admin_url}/api/v1/payments-admin/order-context"
    return fetch_items("PAYMENTS", url, params={"locker_id": locker_id, "limit": limit})


def _fetch_finance_resolve(code: str) -> dict[str, Any] | None:
    if not code:
        return None
    s = _settings()
    url = f"{s.finance_admin_url}/api/v1/finance-admin/locker-network-catalog/resolve/{code}"
    try:
        result = fetch_json("FINANCE", url)
        return result if isinstance(result, dict) else None
    except DomainHttpError:
        return None


def _fetch_partner_players() -> list[dict[str, Any]]:
    s = _settings()
    url = f"{s.partner_admin_url}/api/v1/partner-admin/ecosystem/players"
    return fetch_items("PARTNER", url, params={"limit": 500})


def _local_snapshot(db: Session, locker_id: str) -> dict[str, Any]:
    return {
        "marketplace_links": len(
            db.query(HardwareLockerMarketplaceLink)
            .filter(HardwareLockerMarketplaceLink.locker_id == locker_id)
            .all()
        ),
        "payment_bindings": [
            {
                "payment_method_code": b.payment_method_code,
                "payment_provider_code": b.payment_provider_code,
                "is_active": b.is_active,
            }
            for b in db.query(HardwareLockerPaymentBinding)
            .filter(HardwareLockerPaymentBinding.locker_id == locker_id)
            .all()
        ],
        "carrier_bindings": len(
            db.query(HardwareLockerCarrierBinding)
            .filter(HardwareLockerCarrierBinding.locker_id == locker_id)
            .all()
        ),
        "channel_bindings": len(
            db.query(HardwareLockerChannelBinding)
            .filter(HardwareLockerChannelBinding.locker_id == locker_id)
            .all()
        ),
        "domain_references": [
            {
                "id": r.id,
                "domain_type": r.domain_type,
                "external_id": r.external_id,
                "external_code": r.external_code,
            }
            for r in db.query(HardwareDomainReference)
            .filter(HardwareDomainReference.locker_id == locker_id)
            .all()
        ],
    }


def _runtime_row(db: Session, locker_id: str) -> dict[str, Any] | None:
    row = db.query(RuntimeLocker).filter(RuntimeLocker.locker_id == locker_id).first()
    if not row:
        return None
    return {
        "locker_id": row.locker_id,
        "machine_id": row.machine_id,
        "vendor_id": row.vendor_id,
        "status": "ACTIVE" if row.active else "INACTIVE",
        "slot_count": row.slot_count_total,
        "mqtt_locker_id": row.mqtt_locker_id,
        "operator_id": row.operator_id,
    }


def verify_domain_reference(db: Session, ref: HardwareDomainReference) -> DomainReferenceVerificationOut:
    domain = ref.domain_type.upper()
    status = "UNKNOWN"
    detail: str | None = None
    snapshot: dict[str, Any] | None = None

    try:
        if domain == "PAYMENT_GATEWAY":
            methods = _fetch_gateway_methods(ref.locker_id)
            codes = {str(m.get("method") or "") for m in methods}
            if ref.external_id in codes or (ref.external_code and ref.external_code in codes):
                status = "OK"
            elif methods:
                status = "MISMATCH"
                detail = f"gateway has {sorted(codes)}; ref={ref.external_id or ref.external_code}"
            else:
                status = "NOT_FOUND"
                detail = "no payment methods on gateway for locker"
            snapshot = {"methods": methods[:10]}

        elif domain == "ORDER_PICKUP":
            pickups = _fetch_pickups_for_locker(ref.locker_id)
            ids = {str(p.get("id") or "") for p in pickups}
            order_ids = {str(p.get("order_id") or "") for p in pickups}
            if ref.external_id in ids or ref.external_id in order_ids:
                status = "OK"
            elif pickups:
                status = "MISMATCH"
                detail = f"{len(pickups)} pickups on locker; ref id not matched"
            else:
                status = "NOT_FOUND"
                detail = "no pickups for locker in order_pickup_admin"
            snapshot = {"pickups_count": len(pickups)}

        elif domain == "RUNTIME":
            runtime = _runtime_row(db, ref.locker_id)
            if runtime and (
                ref.external_id == runtime["locker_id"] or ref.external_id == runtime.get("machine_id")
            ):
                status = "OK"
            elif runtime:
                status = "MISMATCH"
                detail = f"runtime locker={runtime['locker_id']} machine={runtime.get('machine_id')}"
            else:
                status = "NOT_FOUND"
                detail = "locker not in runtime_lockers_admin"
            snapshot = runtime

        elif domain == "FINANCE":
            code = ref.external_code or ref.external_id
            resolved = _fetch_finance_resolve(code)
            if resolved and resolved.get("catalog_code"):
                status = "OK"
                snapshot = resolved
            else:
                status = "NOT_FOUND"
                detail = f"finance catalog cannot resolve {code}"

        elif domain == "PARTNER":
            players = _fetch_partner_players()
            codes = {str(p.get("player_code") or "") for p in players}
            if ref.external_code in codes or ref.external_id in {str(p.get("id") or "") for p in players}:
                status = "OK"
            elif players:
                status = "MISMATCH"
                detail = "partner ecosystem player not matched"
            else:
                status = "NOT_FOUND"
            snapshot = {"players_total": len(players)}

        elif domain == "ML":
            code = ref.external_code or ref.external_id
            players = _fetch_ml_players(code)
            codes = {str(p.get("code") or p.get("player_code") or "") for p in players}
            if code in codes or ref.external_id in {str(p.get("id") or "") for p in players}:
                status = "OK"
                snapshot = {"matched": players[:3]}
            elif players:
                status = "MISMATCH"
                detail = f"ML players loaded ({len(players)}); ref {code} not matched"
            else:
                status = "NOT_FOUND"
                detail = "ml_admin returned no players"

        elif domain == "FISCAL":
            code = ref.external_code or ref.external_id
            corridor = _fetch_fiscal_corridor(code)
            if corridor and corridor.get("corridor_code"):
                status = "OK"
                snapshot = corridor
            else:
                certs = _fetch_fiscal_certifications(ref.external_id if ref.external_id.startswith("FISC") else None)
                if certs:
                    status = "OK"
                    snapshot = {"certifications_count": len(certs)}
                else:
                    status = "NOT_FOUND"
                    detail = f"fiscal corridor/cert not found for {code}"

        elif domain == "MARKETPLACE":
            partners = _fetch_marketplace_channel_partners()
            codes = {str(p.get("code") or "").upper() for p in partners}
            ref_code = (ref.external_code or ref.external_id or "").upper()
            if ref_code in codes or ref.external_id in {str(p.get("id") or "") for p in partners}:
                status = "OK"
                snapshot = {"partners_total": len(partners)}
            elif partners:
                status = "MISMATCH"
                detail = f"marketplace has {len(partners)} partners; ref not matched"
            else:
                status = "UNREACHABLE"
                detail = "no channel partners from marketplace_admin"

        elif domain in {"FOOD_DELIVERY", "LOGISTICS_PLATFORM"}:
            status = "LOCAL_ONLY" if ref.active else "INACTIVE"
            detail = "verified locally; no live HTTP probe for this domain type"

        else:
            status = "UNSUPPORTED"
            detail = f"no verifier for domain_type={domain}"

    except DomainHttpError as exc:
        status = "UNREACHABLE"
        detail = exc.detail

    return DomainReferenceVerificationOut(
        reference_id=ref.id,
        locker_id=ref.locker_id,
        domain_type=ref.domain_type,
        external_id=ref.external_id,
        external_code=ref.external_code,
        status=status,
        detail=detail,
        remote_snapshot=snapshot,
    )


def verify_domain_references(
    db: Session, *, locker_id: str | None = None
) -> list[DomainReferenceVerificationOut]:
    q = db.query(HardwareDomainReference)
    if locker_id:
        q = q.filter(HardwareDomainReference.locker_id == locker_id)
    return [verify_domain_reference(db, ref) for ref in q.all()]


def _gaps_for_locker(db: Session, locker_id: str) -> list[CrossDomainGapItemOut]:
    gaps: list[CrossDomainGapItemOut] = []

    if not _runtime_row(db, locker_id):
        gaps.append(
            CrossDomainGapItemOut(
                locker_id=locker_id,
                gap_type="MISSING_RUNTIME",
                severity="HIGH",
                message="Locker ausente em runtime_lockers_admin",
                suggested_action="Cadastrar em Runtime ou reconciliar com backend/runtime",
            )
        )

    refs = db.query(HardwareDomainReference).filter(HardwareDomainReference.locker_id == locker_id).all()
    ref_types = {r.domain_type for r in refs if r.active}
    for expected, msg, action in [
        ("ORDER_PICKUP", "Sem referência ORDER_PICKUP", "POST /cross-domain/domain-references"),
        ("PAYMENT_GATEWAY", "Sem referência PAYMENT_GATEWAY", "Sync payment bindings + criar domain ref"),
    ]:
        if expected not in ref_types:
            gaps.append(
                CrossDomainGapItemOut(
                    locker_id=locker_id,
                    gap_type=f"MISSING_{expected}",
                    severity="MEDIUM",
                    message=msg,
                    suggested_action=action,
                )
            )

    hw_payments = {
        b.payment_method_code
        for b in db.query(HardwareLockerPaymentBinding)
        .filter(HardwareLockerPaymentBinding.locker_id == locker_id, HardwareLockerPaymentBinding.is_active.is_(True))
        .all()
    }
    if not hw_payments:
        gaps.append(
            CrossDomainGapItemOut(
                locker_id=locker_id,
                gap_type="NO_PAYMENT_BINDINGS",
                severity="MEDIUM",
                message="Nenhum método de pagamento vinculado ao locker",
                suggested_action="POST /cross-domain/payment-bindings/sync-from-gateway",
            )
        )

    try:
        gw = {str(m.get("method") or "") for m in _fetch_gateway_methods(locker_id)}
        only_hw = sorted(hw_payments - gw)
        only_gw = sorted(gw - hw_payments)
        if only_hw:
            gaps.append(
                CrossDomainGapItemOut(
                    locker_id=locker_id,
                    gap_type="PAYMENT_HW_ONLY",
                    severity="LOW",
                    message=f"Métodos só no hardware: {', '.join(only_hw)}",
                    suggested_action="Revisar ou desativar bindings órfãos",
                )
            )
        if only_gw:
            gaps.append(
                CrossDomainGapItemOut(
                    locker_id=locker_id,
                    gap_type="PAYMENT_GATEWAY_ONLY",
                    severity="MEDIUM",
                    message=f"Métodos só no gateway: {', '.join(only_gw)}",
                    suggested_action="POST /cross-domain/payment-bindings/sync-from-gateway",
                )
            )
    except DomainHttpError:
        gaps.append(
            CrossDomainGapItemOut(
                locker_id=locker_id,
                gap_type="PAYMENT_GATEWAY_UNREACHABLE",
                severity="HIGH",
                message="Payment gateway admin indisponível para comparar métodos",
                suggested_action="Subir payment_gateway_admin_service :8017",
            )
        )

    if not db.query(HardwareLockerMarketplaceLink).filter(
        HardwareLockerMarketplaceLink.locker_id == locker_id,
        HardwareLockerMarketplaceLink.active.is_(True),
    ).first():
        gaps.append(
            CrossDomainGapItemOut(
                locker_id=locker_id,
                gap_type="NO_MARKETPLACE_LINK",
                severity="LOW",
                message="Locker sem vínculo marketplace ativo",
                suggested_action="POST /cross-domain/marketplace-links",
            )
        )

    return gaps


def scan_cross_domain_gaps(db: Session, *, locker_id: str | None = None) -> CrossDomainGapsScanOut:
    locker_ids = [locker_id] if locker_id else _collect_locker_ids(db)
    all_gaps: list[CrossDomainGapItemOut] = []
    for lid in locker_ids:
        all_gaps.extend(_gaps_for_locker(db, lid))
    return CrossDomainGapsScanOut(
        lockers_scanned=len(locker_ids),
        gaps=all_gaps,
        total=len(all_gaps),
        domain_reachability=probe_domain_reachability(),
    )


def get_locker_360(db: Session, locker_id: str) -> Locker360Out:
    local = _local_snapshot(db, locker_id)
    remote = Locker360RemoteOut()
    verifications = verify_domain_references(db, locker_id=locker_id)

    try:
        gw_methods = _fetch_gateway_methods(locker_id)
        remote.payment_gateway = {"reachable": True, "methods": gw_methods, "total": len(gw_methods)}
    except DomainHttpError as exc:
        remote.payment_gateway = {"reachable": False, "error": exc.detail}

    try:
        pickups = _fetch_pickups_for_locker(locker_id)
        remote.order_pickup = {"reachable": True, "pickups": pickups[:20], "total": len(pickups)}
    except DomainHttpError as exc:
        remote.order_pickup = {"reachable": False, "error": exc.detail}

    try:
        contexts = _fetch_payment_contexts(locker_id)
        remote.payments_context = {"reachable": True, "contexts": contexts[:20], "total": len(contexts)}
    except DomainHttpError as exc:
        remote.payments_context = {"reachable": False, "error": exc.detail}

    finance_codes: list[str] = []
    for player in db.query(HardwareEcosystemPlayer).filter(HardwareEcosystemPlayer.is_active.is_(True)).all():
        if player.finance_catalog_code:
            finance_codes.append(player.finance_catalog_code)
    resolved: list[dict[str, Any]] = []
    for code in finance_codes[:5]:
        hit = _fetch_finance_resolve(code)
        if hit:
            resolved.append(hit)
    remote.finance_catalog = {"resolved_samples": resolved, "codes_checked": finance_codes[:5]}

    try:
        partners = _fetch_partner_players()
        remote.partner_ecosystem = {"reachable": True, "players_total": len(partners)}
    except DomainHttpError as exc:
        remote.partner_ecosystem = {"reachable": False, "error": exc.detail}

    try:
        mkt_partners = _fetch_marketplace_channel_partners()
        remote.marketplace = {"reachable": True, "channel_partners": mkt_partners[:15], "total": len(mkt_partners)}
    except DomainHttpError as exc:
        remote.marketplace = {"reachable": False, "error": exc.detail}

    try:
        ml_players = _fetch_ml_players()
        remote.ml = {"reachable": True, "network_players": ml_players[:15], "total": len(ml_players)}
    except DomainHttpError as exc:
        remote.ml = {"reachable": False, "error": exc.detail}

    try:
        corridors = fetch_items(
            "FISCAL",
            f"{_settings().fiscal_admin_url}/api/v1/fiscal-admin/fiscal-global-ops/corridors",
            params={"active_only": True},
        )
        certs = _fetch_fiscal_certifications()
        remote.fiscal = {
            "reachable": True,
            "corridors_count": len(corridors),
            "certifications_count": len(certs),
            "corridors_sample": corridors[:5],
        }
    except DomainHttpError as exc:
        remote.fiscal = {"reachable": False, "error": exc.detail}

    gaps = _gaps_for_locker(db, locker_id)
    return Locker360Out(
        locker_id=locker_id,
        runtime=_runtime_row(db, locker_id),
        local=local,
        remote=remote,
        gaps=gaps,
        domain_verifications=verifications,
    )


def sync_payment_bindings_from_gateway(
    db: Session,
    *,
    locker_id: str | None = None,
    dry_run: bool = False,
) -> PaymentBindingSyncOut:
    methods = _fetch_gateway_methods(locker_id)
    target_lockers = {locker_id} if locker_id else {str(m.get("locker_id") or "") for m in methods}
    target_lockers.discard("")

    inserted = updated = skipped = 0
    hardware_only: list[str] = []
    conflicts: list[dict[str, Any]] = []

    for lid in sorted(target_lockers):
        gw_for_locker = [m for m in methods if str(m.get("locker_id") or "") == lid]
        gw_codes = {str(m.get("method") or "") for m in gw_for_locker}

        existing = {
            b.payment_method_code: b
            for b in db.query(HardwareLockerPaymentBinding)
            .filter(HardwareLockerPaymentBinding.locker_id == lid)
            .all()
        }

        for code in sorted(existing.keys() - gw_codes):
            hardware_only.append(f"{lid}:{code}")

        for method_row in gw_for_locker:
            code = str(method_row.get("method") or "")
            if not code:
                skipped += 1
                continue
            is_active = bool(method_row.get("is_active", True))
            row = existing.get(code)
            if row:
                if row.is_active != is_active:
                    if not dry_run:
                        row.is_active = is_active
                    updated += 1
                else:
                    skipped += 1
            else:
                if not dry_run:
                    db.add(
                        HardwareLockerPaymentBinding(
                            id=new_id(),
                            locker_id=lid,
                            payment_method_code=code,
                            payment_provider_code=None,
                            is_active=is_active,
                            metadata_json={"source": "PAYMENT_GATEWAY_SYNC"},
                        )
                    )
                inserted += 1

        for code, row in existing.items():
            if code not in gw_codes and row.is_active:
                conflicts.append(
                    {
                        "locker_id": lid,
                        "payment_method_code": code,
                        "issue": "active_in_hardware_missing_on_gateway",
                    }
                )

    if not dry_run:
        db.commit()

    return PaymentBindingSyncOut(
        locker_id=locker_id,
        dry_run=dry_run,
        gateway_methods=len(methods),
        inserted=inserted,
        updated=updated,
        skipped=skipped,
        hardware_only=hardware_only,
        conflicts=conflicts,
    )


def align_ecosystem_with_partner(db: Session, *, apply: bool = False) -> EcosystemAlignmentOut:
    try:
        partner_players = _fetch_partner_players()
    except DomainHttpError:
        partner_players = []

    by_finance: dict[str, dict[str, Any]] = {}
    by_operator: dict[str, dict[str, Any]] = {}
    for p in partner_players:
        fc = str(p.get("finance_catalog_code") or "").upper()
        op = str(p.get("locker_operator_ref") or "").upper()
        if fc:
            by_finance[fc] = p
        if op:
            by_operator[op] = p

    matched: list[EcosystemAlignmentItemOut] = []
    unmatched: list[str] = []
    metadata_updated = 0

    for hw in db.query(HardwareEcosystemPlayer).order_by(HardwareEcosystemPlayer.player_code).all():
        partner: dict[str, Any] | None = None
        match_field: str | None = None
        fc = (hw.finance_catalog_code or "").upper()
        op = (hw.operator_id or "").upper()
        if fc and fc in by_finance:
            partner = by_finance[fc]
            match_field = "finance_catalog_code"
        elif op and op in by_operator:
            partner = by_operator[op]
            match_field = "locker_operator_ref"

        if partner:
            matched.append(
                EcosystemAlignmentItemOut(
                    hardware_player_code=hw.player_code,
                    hardware_player_id=hw.id,
                    partner_player_code=str(partner.get("player_code") or ""),
                    partner_player_id=str(partner.get("id") or ""),
                    match_field=match_field,
                    finance_catalog_code=hw.finance_catalog_code,
                    locker_operator_ref=hw.operator_id,
                )
            )
            if apply:
                meta = dict(hw.metadata_json or {})
                prev = meta.get("partner_ecosystem_player_id")
                pid = str(partner.get("id") or "")
                if prev != pid:
                    meta["partner_ecosystem_player_id"] = pid
                    meta["partner_ecosystem_player_code"] = partner.get("player_code")
                    meta["alignment_source"] = "PARTNER_ADMIN_HTTP"
                    hw.metadata_json = meta
                    metadata_updated += 1
        else:
            unmatched.append(hw.player_code)

    if apply and metadata_updated:
        db.commit()

    return EcosystemAlignmentOut(
        matched=matched,
        unmatched_hardware=unmatched,
        apply=apply,
        metadata_updated=metadata_updated,
    )

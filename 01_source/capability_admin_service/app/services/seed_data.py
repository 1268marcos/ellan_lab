from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.capability import (
    CapabilityChannel,
    CapabilityContext,
    CapabilityProfile,
    CapabilityRegion,
    PaymentInterfaceCatalog,
    PaymentMethodCatalog,
    WalletProviderCatalog,
)
from app.models.capability import CapabilityProfileAction, CapabilityProfileConstraint, CapabilityProfileMethod
from app.models.ecosystem import (
    CapabilityEcosystemPlayer,
    CapabilityProfilePlayerBinding,
)
from app.models.geo import CapabilityCountry, CapabilityProvince
from app.services.ecosystem_service import bind_player
from app.services.intelligence_service import recompute_intelligence, seed_intelligence_baseline
from app.services.ops_service import seed_default_templates
from app.services.seed_global_ecosystem import seed_global_ecosystem


def run_seed(db: Session) -> dict[str, int]:
    counts = {
        k: 0
        for k in (
            "channels",
            "contexts",
            "regions",
            "methods",
            "interfaces",
            "wallets",
            "countries",
            "provinces",
            "profiles",
            "segments",
            "players",
            "bindings",
            "actions",
            "constraints",
            "integration_modes",
            "player_integrations",
            "player_relations",
            "locker_presences",
            "feature_flags",
            "corridors",
            "templates",
        )
    }

    channels_spec = [
        ("kiosk", "Kiosk presencial", "Totem / locker físico"),
        ("online", "E-commerce", "Checkout web e app"),
        ("partner", "Parceiro B2B", "Integrações marketplace / carrier"),
        ("staff", "Operação interna", "Liberação assistida"),
        ("marketplace", "Marketplace hub", "Magalu, ML, Amazon Hub"),
        ("carrier", "Carrier global", "DHL, DPD, InPost, Correios"),
    ]
    channel_map: dict[str, CapabilityChannel] = {}
    for code, name, desc in channels_spec:
        row = db.query(CapabilityChannel).filter(CapabilityChannel.code == code).first()
        if not row:
            row = CapabilityChannel(code=code, name=name, description=desc, is_active=True)
            db.add(row)
            db.flush()
            counts["channels"] += 1
        channel_map[code] = row

    contexts_spec = [
        ("kiosk", "purchase", "Compra presencial"),
        ("kiosk", "pickup", "Retirada de pedido"),
        ("kiosk", "return_dropoff", "Devolução"),
        ("online", "checkout", "Checkout online"),
        ("online", "pickup_schedule", "Agendamento retirada"),
        ("partner", "webhook_payment", "Webhook pagamento"),
        ("marketplace", "order_ingest", "Ingestão pedido marketplace"),
        ("carrier", "label_dropoff", "Depósito carrier"),
        ("staff", "manual_release", "Liberação manual"),
    ]
    for ch_code, ctx_code, name in contexts_spec:
        ch = channel_map[ch_code]
        exists = (
            db.query(CapabilityContext)
            .filter(CapabilityContext.channel_id == ch.id, CapabilityContext.code == ctx_code)
            .first()
        )
        if not exists:
            db.add(CapabilityContext(channel_id=ch.id, code=ctx_code, name=name, is_active=True))
            counts["contexts"] += 1

    regions_spec = [
        ("SP", "São Paulo", "BR", "South America", "BRL"),
        ("PT", "Portugal", "PT", "Europe", "EUR"),
        ("ES", "Espanha", "ES", "Europe", "EUR"),
        ("UK", "Reino Unido", "GB", "Europe", "GBP"),
        ("US", "Estados Unidos", "US", "North America", "USD"),
        ("DE", "Alemanha", "DE", "Europe", "EUR"),
        ("PL", "Polônia", "PL", "Europe", "PLN"),
    ]
    region_map: dict[str, CapabilityRegion] = {}
    for code, name, cc, cont, cur in regions_spec:
        row = db.query(CapabilityRegion).filter(CapabilityRegion.code == code).first()
        if not row:
            row = CapabilityRegion(
                code=code,
                name=name,
                country_code=cc,
                continent=cont,
                default_currency=cur,
                is_active=True,
                metadata_json={"players": ["InPost", "DHL", "DPD", "Magalu", "MercadoLivre"]},
            )
            db.add(row)
            db.flush()
            counts["regions"] += 1
        region_map[code] = row

    methods_spec = [
        ("pix", "PIX", "bank_transfer", False, False, False, False, True, True),
        ("creditCard", "Cartão de Crédito", "card", False, True, False, False, False, False),
        ("debitCard", "Cartão de Débito", "card", False, True, False, False, False, False),
        ("mbway", "MB Way", "digital_wallet", True, False, False, False, False, True),
        ("apple_pay", "Apple Pay", "digital_wallet", True, True, False, False, False, False),
        ("google_pay", "Google Pay", "digital_wallet", True, True, False, False, False, False),
        ("cash", "Dinheiro", "cash", False, False, False, True, False, False),
    ]
    for code, name, family, iw, ic, ib, icash, ibt, inst in methods_spec:
        if not db.query(PaymentMethodCatalog).filter(PaymentMethodCatalog.code == code).first():
            db.add(
                PaymentMethodCatalog(
                    code=code,
                    name=name,
                    family=family,
                    is_wallet=iw,
                    is_card=ic,
                    is_bnpl=ib,
                    is_cash_like=icash,
                    is_bank_transfer=ibt,
                    is_instant=inst,
                    is_active=True,
                )
            )
            counts["methods"] += 1

    for code, name, itype in [
        ("qr_code", "QR Code", "digital"),
        ("nfc", "NFC", "physical"),
        ("chip", "Chip EMV", "physical"),
        ("kiosk_pinpad", "PinPad Kiosk", "physical"),
    ]:
        if not db.query(PaymentInterfaceCatalog).filter(PaymentInterfaceCatalog.code == code).first():
            db.add(PaymentInterfaceCatalog(code=code, name=name, interface_type=itype, is_active=True))
            counts["interfaces"] += 1

    for code, name in [
        ("mercadoPago", "Mercado Pago"),
        ("picpay", "PicPay"),
        ("mbway", "MB Way"),
        ("applePay", "Apple Pay"),
    ]:
        if not db.query(WalletProviderCatalog).filter(WalletProviderCatalog.code == code).first():
            db.add(WalletProviderCatalog(code=code, name=name, is_active=True))
            counts["wallets"] += 1

    countries_spec = [
        ("BR", "Brasil", "South America", "BRL"),
        ("PT", "Portugal", "Europe", "EUR"),
        ("ES", "Espanha", "Europe", "EUR"),
        ("GB", "Reino Unido", "Europe", "GBP"),
        ("US", "Estados Unidos", "North America", "USD"),
        ("DE", "Alemanha", "Europe", "EUR"),
        ("PL", "Polônia", "Europe", "PLN"),
    ]
    for code, name, cont, cur in countries_spec:
        if not db.query(CapabilityCountry).filter(CapabilityCountry.code == code).first():
            db.add(CapabilityCountry(code=code, name=name, continent=cont, default_currency=cur, is_active=True))
            counts["countries"] += 1

    provinces_spec = [
        ("BR-SP", "São Paulo", "BR"),
        ("BR-RJ", "Rio de Janeiro", "BR"),
        ("PT-11", "Lisboa", "PT"),
        ("ES-M", "Madrid", "ES"),
        ("GB-LON", "Greater London", "GB"),
        ("DE-BE", "Berlim", "DE"),
    ]
    for code, name, cc in provinces_spec:
        if not db.query(CapabilityProvince).filter(CapabilityProvince.code == code).first():
            db.add(CapabilityProvince(code=code, name=name, country_code=cc, is_active=True))
            counts["provinces"] += 1

    db.flush()
    channels = {c.code: c for c in db.query(CapabilityChannel).all()}
    contexts = {}
    for ctx in db.query(CapabilityContext).all():
        ch = db.get(CapabilityChannel, ctx.channel_id)
        if ch:
            contexts[f"{ch.code}:{ctx.code}"] = ctx
    regions = {r.code: r for r in db.query(CapabilityRegion).all()}

    profiles_spec = [
        ("SP", "kiosk", "purchase", "SP:kiosk:purchase", "São Paulo Kiosk Compra", "BRL"),
        ("SP", "kiosk", "pickup", "SP:kiosk:pickup", "São Paulo Kiosk Retirada", "BRL"),
        ("PT", "kiosk", "purchase", "PT:kiosk:purchase", "Portugal Kiosk Compra", "EUR"),
        ("UK", "online", "checkout", "UK:online:checkout", "UK Online Checkout", "GBP"),
        ("DE", "carrier", "label_dropoff", "DE:carrier:dropoff", "DHL Packstation DE", "EUR"),
    ]
    for reg, ch, ctx, pcode, pname, cur in profiles_spec:
        if not db.query(CapabilityProfile).filter(CapabilityProfile.profile_code == pcode).first():
            db.add(
                CapabilityProfile(
                    region_id=regions[reg].id,
                    channel_id=channels[ch].id,
                    context_id=contexts[f"{ch}:{ctx}"].id,
                    profile_code=pcode,
                    name=pname,
                    currency=cur,
                    priority=100,
                    is_active=True,
                    metadata_json={"seed": True, "players": json.dumps(["InPost", "DPD", "Magalu"])},
                )
            )
            counts["profiles"] += 1

    global_counts = seed_global_ecosystem(db)
    for k in (
        "segments",
        "players",
        "integration_modes",
        "player_integrations",
        "player_relations",
        "locker_presences",
    ):
        counts[k] += global_counts.get(k, 0)

    player_map: dict[str, CapabilityEcosystemPlayer] = {
        p.code: p for p in db.query(CapabilityEcosystemPlayer).all()
    }

    db.flush()
    profile_by_code = {p.profile_code: p for p in db.query(CapabilityProfile).all()}
    pix = db.query(PaymentMethodCatalog).filter(PaymentMethodCatalog.code == "pix").first()

    bindings_spec = [
        ("SP:kiosk:purchase", "MAGALU", "PRIMARY"),
        ("SP:kiosk:purchase", "MELI", "FALLBACK"),
        ("SP:kiosk:purchase", "CORREIOS", "LOCKER_POSTAL"),
        ("SP:kiosk:pickup", "CORREIOS", "PRIMARY"),
        ("SP:kiosk:pickup", "MELI", "FALLBACK"),
        ("PT:kiosk:purchase", "CTT", "PRIMARY"),
        ("PT:kiosk:purchase", "WORTEN", "FALLBACK"),
        ("PT:kiosk:purchase", "EL_CORTE_INGLES", "LOCKER_RETAIL"),
        ("DE:carrier:dropoff", "DHL", "PRIMARY"),
        ("DE:carrier:dropoff", "DPD", "FALLBACK"),
        ("DE:carrier:dropoff", "INPOST", "LOCKER_NETWORK"),
        ("UK:online:checkout", "AMAZON", "PRIMARY"),
        ("UK:online:checkout", "INPOST", "LOCKER_NETWORK"),
    ]
    for pcode, player_code, role in bindings_spec:
        prof = profile_by_code.get(pcode)
        player = player_map.get(player_code)
        if prof and player:
            exists = (
                db.query(CapabilityProfilePlayerBinding)
                .filter(
                    CapabilityProfilePlayerBinding.profile_id == prof.id,
                    CapabilityProfilePlayerBinding.player_id == player.id,
                )
                .first()
            )
            if not exists:
                bind_player(db, profile_id=prof.id, player_id=player.id, binding_role=role)
                counts["bindings"] += 1

    for pcode in ("SP:kiosk:purchase", "PT:kiosk:purchase"):
        prof = profile_by_code.get(pcode)
        if not prof:
            continue
        if not db.query(CapabilityProfileAction).filter(
            CapabilityProfileAction.profile_id == prof.id, CapabilityProfileAction.action_code == "pay"
        ).first():
            db.add(
                CapabilityProfileAction(
                    profile_id=prof.id,
                    action_code="pay",
                    label="Pagar",
                    sort_order=10,
                    is_active=True,
                )
            )
            counts["actions"] += 1
        if pix and not db.query(CapabilityProfileMethod).filter(
            CapabilityProfileMethod.profile_id == prof.id,
            CapabilityProfileMethod.payment_method_id == pix.id,
        ).first():
            db.add(
                CapabilityProfileMethod(
                    profile_id=prof.id,
                    payment_method_id=pix.id,
                    sort_order=10,
                    is_default=True,
                    is_active=True,
                )
            )
        if not db.query(CapabilityProfileConstraint).filter(
            CapabilityProfileConstraint.profile_id == prof.id,
            CapabilityProfileConstraint.code == "max_amount",
        ).first():
            db.add(
                CapabilityProfileConstraint(
                    profile_id=prof.id,
                    code="max_amount",
                    value_json={"amount": 5000, "currency": prof.currency},
                )
            )
            counts["constraints"] += 1

    intel_counts = seed_intelligence_baseline(db)
    for k in ("feature_flags", "corridors"):
        counts[k] += intel_counts.get(k, 0)

    counts["templates"] += seed_default_templates(db)

    db.commit()
    recompute_intelligence(db)
    return counts

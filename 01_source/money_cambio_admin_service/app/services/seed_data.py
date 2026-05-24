from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.cambio import CambioFxRate
from app.models.catalog import (
    PaymentInterfaceCatalog,
    PaymentMethodCatalog,
    PaymentMethodUiAlias,
    WalletProviderCatalog,
)
from app.models.integration import MoneyCambioIntegrationPartner
from app.models.money import MoneyCurrencyCatalog
from app.models.professional import (
    CambioPaymentCorridor,
    MoneyComplianceLimit,
    MoneyMethodCountryMatrix,
    MoneyOperatingCountry,
    MoneyWalletCountryMatrix,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def run_seed(db: Session) -> dict[str, int]:
    counts = {
        "currencies": 0,
        "methods": 0,
        "interfaces": 0,
        "aliases": 0,
        "wallets": 0,
        "fx_rates": 0,
        "partners": 0,
        "countries": 0,
        "method_matrix": 0,
        "wallet_matrix": 0,
        "corridors": 0,
        "compliance": 0,
        "locker_players": 0,
        "countries_updated": 0,
    }

    currencies = [
        ("BRL", "Real brasileiro", "R$", "986", "LATAM"),
        ("USD", "Dólar americano", "$", "840", "AMERICAS"),
        ("EUR", "Euro", "€", "978", "EU"),
        ("GBP", "Libra esterlina", "£", "826", "EU"),
        ("PLN", "Złoty polonês", "zł", "985", "EU"),
        ("MXN", "Peso mexicano", "$", "484", "LATAM"),
        ("INR", "Rupia indiana", "₹", "356", "APAC"),
        ("CNY", "Yuan chinês", "¥", "156", "APAC"),
        ("JPY", "Iene japonês", "¥", "392", "APAC"),
        ("KES", "Xelim queniano", "KSh", "404", "AFRICA"),
    ]
    for code, name, symbol, numeric, region in currencies:
        if not db.query(MoneyCurrencyCatalog).filter(MoneyCurrencyCatalog.code == code).first():
            db.add(
                MoneyCurrencyCatalog(
                    code=code,
                    name=name,
                    symbol=symbol,
                    numeric_code=numeric,
                    region_hint=region,
                    is_active=True,
                )
            )
            counts["currencies"] += 1

    methods = [
        ("PIX", "PIX instantâneo", "instant", dict(is_instant=True)),
        ("CREDIT_CARD", "Cartão de crédito", "card", dict(is_card=True)),
        ("DEBIT_CARD", "Cartão de débito", "card", dict(is_card=True)),
        ("M_PESA", "M-Pesa", "mobile_money", dict(is_wallet=True, is_instant=True)),
        ("PAYPAL", "PayPal", "wallet", dict(is_wallet=True)),
        ("BOLETO", "Boleto", "bank_transfer", dict(is_bank_transfer=True)),
    ]
    for code, name, family, flags in methods:
        if not db.query(PaymentMethodCatalog).filter(PaymentMethodCatalog.code == code).first():
            db.add(PaymentMethodCatalog(code=code, name=name, family=family, is_active=True, **flags))
            counts["methods"] += 1

    if not db.query(PaymentInterfaceCatalog).filter(PaymentInterfaceCatalog.code == "TOTEM_TOUCH").first():
        db.add(
            PaymentInterfaceCatalog(
                code="TOTEM_TOUCH",
                name="Totem touch",
                interface_type="TOTEM",
                requires_hw=True,
                is_active=True,
            )
        )
        counts["interfaces"] += 1

    if not db.get(PaymentMethodUiAlias, "alias-pix-totem"):
        db.add(
            PaymentMethodUiAlias(
                id="alias-pix-totem",
                ui_code="PIX_QR",
                canonical_method_code="PIX",
                default_payment_interface_code="TOTEM_TOUCH",
                is_active=True,
            )
        )
        counts["aliases"] += 1

    wallets = [
        ("MERCADOPAGO", "Mercado Pago"),
        ("STRIPE", "Stripe Wallet"),
        ("PAYPAL", "PayPal"),
        ("M_PESA", "M-Pesa"),
        ("ALIPAY", "Alipay"),
        ("WECHAT_PAY", "WeChat Pay"),
    ]
    for code, name in wallets:
        if not db.query(WalletProviderCatalog).filter(WalletProviderCatalog.code == code).first():
            db.add(WalletProviderCatalog(code=code, name=name, is_active=True))
            counts["wallets"] += 1

    today = date.today()
    fx_pairs = [
        ("USD", "BRL", Decimal("5.05000000")),
        ("EUR", "BRL", Decimal("5.45000000")),
        ("EUR", "USD", Decimal("1.08000000")),
        ("GBP", "EUR", Decimal("1.17000000")),
        ("USD", "MXN", Decimal("17.20000000")),
        ("USD", "PLN", Decimal("3.95000000")),
    ]
    for base, quote, rate in fx_pairs:
        exists = (
            db.query(CambioFxRate)
            .filter(
                CambioFxRate.base_currency == base,
                CambioFxRate.quote_currency == quote,
                CambioFxRate.rate_date == today,
            )
            .first()
        )
        if not exists:
            db.add(
                CambioFxRate(
                    id=new_id(),
                    base_currency=base,
                    quote_currency=quote,
                    rate_date=today,
                    rate=rate,
                    source="SEED",
                )
            )
            counts["fx_rates"] += 1

    partners = [
        ("mc-ecb-001", "ECB FX Feed", "ECB-FX", "FX_FEED", "EU", "EUR"),
        ("mc-openex-001", "Open Exchange Rates", "OPENEX", "FX_AGGREGATOR", "US", "USD"),
        ("mc-wise-001", "Wise Business", "WISE", "TREASURY", "GB", "GBP"),
    ]
    for pid, name, code, ptype, country, ccy in partners:
        if not db.query(MoneyCambioIntegrationPartner).filter(MoneyCambioIntegrationPartner.code == code).first():
            db.add(
                MoneyCambioIntegrationPartner(
                    id=pid,
                    name=name,
                    code=code,
                    partner_type=ptype,
                    country=country,
                    default_currency=ccy,
                    api_base_url=f"https://api.example/{code.lower()}",
                    active=True,
                )
            )
            counts["partners"] += 1

    countries = [
        ("BR", "Brasil", "South America", "BRL", "LATAM", ["pt"], ["Magalu", "Mercado Livre"]),
        ("US", "Estados Unidos", "North America", "USD", "NA", ["en"], ["Amazon Hub", "USPS"]),
        ("GB", "Reino Unido", "Europe", "GBP", "EU", ["en"], ["Royal Mail", "InPost UK"]),
        ("DE", "Alemanha", "Europe", "EUR", "EU", ["de"], ["DHL Packstation", "Hermes DE"]),
        ("FR", "França", "Europe", "EUR", "EU", ["fr"], ["Colissimo", "La Poste"]),
        ("PL", "Polônia", "Europe", "PLN", "EU", ["pl"], ["InPost PL", "DPD PL"]),
        ("PT", "Portugal", "Europe", "EUR", "EU", ["pt"], ["CTT", "Worten"]),
        ("ES", "Espanha", "Europe", "EUR", "EU", ["es"], ["El Corte Inglés", "Correos"]),
        ("MX", "México", "North America", "MXN", "LATAM", ["es"], ["Mercado Libre MX"]),
        ("IN", "Índia", "Asia", "INR", "APAC", ["hi", "en"], ["Flipkart", "Blue Dart"]),
        ("CN", "China", "Asia", "CNY", "APAC", ["zh"], ["Cainiao", "Alipay"]),
        ("JP", "Japão", "Asia", "JPY", "APAC", ["ja"], ["Rakuten"]),
        ("KE", "Quênia", "Africa", "KES", "MEA", ["sw", "en"], ["M-Pesa"]),
        ("NG", "Nigéria", "Africa", "NGN", "MEA", ["en"], ["Airtel Money"]),
        ("AU", "Austrália", "Oceania", "AUD", "APAC", ["en"], ["Australia Post"]),
        ("CH", "Suíça", "Europe", "CHF", "EU", ["de", "fr"], ["Swiss Post"]),
        ("SE", "Suécia", "Europe", "SEK", "EU", ["sv"], ["PostNord", "Bring"]),
        ("AE", "Emirados", "Asia", "AED", "MEA", ["ar", "en"], ["Aramex"]),
    ]
    for cc, name, continent, ccy, zone, langs, networks in countries:
        if not db.query(MoneyOperatingCountry).filter(MoneyOperatingCountry.country_code == cc).first():
            db.add(
                MoneyOperatingCountry(
                    country_code=cc,
                    name=name,
                    continent=continent,
                    default_currency_code=ccy,
                    regulatory_zone=zone,
                    primary_languages_json=langs,
                    locker_networks_json=networks,
                    is_active=True,
                )
            )
            counts["countries"] += 1

    matrix_rows = [
        ("BR", "PIX", 100, 50000000, True, 1000000),
        ("BR", "CREDIT_CARD", 500, None, False, 500000),
        ("BR", "BOLETO", 1000, 10000000, False, None),
        ("US", "CREDIT_CARD", 100, None, False, 300000),
        ("US", "DEBIT_CARD", 100, None, False, 300000),
        ("US", "PAYPAL", 100, 2500000, True, None),
        ("GB", "CREDIT_CARD", 100, None, False, 250000),
        ("DE", "CREDIT_CARD", 100, None, False, 250000),
        ("PL", "CREDIT_CARD", 100, None, False, 200000),
        ("KE", "M_PESA", 50, 1500000, True, 500000),
        ("IN", "CREDIT_CARD", 100, None, False, 200000),
        ("CN", "CREDIT_CARD", 100, None, False, 200000),
    ]
    for country, method, min_c, max_c, instant, kyc in matrix_rows:
        exists = (
            db.query(MoneyMethodCountryMatrix)
            .filter(
                MoneyMethodCountryMatrix.country_code == country,
                MoneyMethodCountryMatrix.payment_method_code == method,
            )
            .first()
        )
        if not exists:
            db.add(
                MoneyMethodCountryMatrix(
                    country_code=country,
                    payment_method_code=method,
                    min_amount_cents=min_c,
                    max_amount_cents=max_c,
                    is_instant_settlement=instant,
                    requires_kyc_above_cents=kyc,
                    sort_order=10 if instant else 100,
                    is_active=True,
                )
            )
            counts["method_matrix"] += 1

    wallet_matrix = [
        ("BR", "MERCADOPAGO"),
        ("US", "PAYPAL"),
        ("US", "STRIPE"),
        ("KE", "M_PESA"),
        ("CN", "ALIPAY"),
        ("CN", "WECHAT_PAY"),
    ]
    for country, wallet in wallet_matrix:
        if not (
            db.query(MoneyWalletCountryMatrix)
            .filter(
                MoneyWalletCountryMatrix.country_code == country,
                MoneyWalletCountryMatrix.wallet_provider_code == wallet,
            )
            .first()
        ):
            db.add(MoneyWalletCountryMatrix(country_code=country, wallet_provider_code=wallet, is_active=True))
            counts["wallet_matrix"] += 1

    corridors = [
        ("BR-US-ECOM", "Brasil → EUA e-commerce", "BR", "US", "BRL", "USD", "CROSS_BORDER", 120, "OPENEX"),
        ("BR-EU-LOCKER", "Brasil → UE locker payout", "BR", "DE", "BRL", "EUR", "CROSS_BORDER", 85, "ECB-FX"),
        ("EU-GB-POST", "UE → UK postal", "DE", "GB", "EUR", "GBP", "CROSS_BORDER", 45, "WISE"),
        ("US-MX-RETAIL", "EUA → México retail", "US", "MX", "USD", "MXN", "CROSS_BORDER", 95, "OPENEX"),
        ("KE-INTL-REMIT", "Quênia remessas", "KE", "GB", "KES", "GBP", "WALLET_PAYOUT", 150, "WISE"),
        ("IN-APAC-TRADE", "Índia APAC trade", "IN", "CN", "INR", "CNY", "CROSS_BORDER", 110, None),
        ("PL-EU-INPOST", "Polônia InPost EU", "PL", "DE", "PLN", "EUR", "DOMESTIC_FX", 25, "ECB-FX"),
        ("BR-BR-DOMESTIC", "Brasil doméstico", "BR", "BR", "BRL", "BRL", "DOMESTIC_FX", 0, None),
    ]
    for code, name, orig, dest, tx, settle, ctype, spread, partner in corridors:
        if not db.query(CambioPaymentCorridor).filter(CambioPaymentCorridor.corridor_code == code).first():
            db.add(
                CambioPaymentCorridor(
                    id=new_id(),
                    corridor_code=code,
                    name=name,
                    origin_country_code=orig,
                    destination_country_code=dest,
                    transaction_currency=tx,
                    settlement_currency=settle,
                    corridor_type=ctype,
                    default_spread_bps=spread,
                    fx_partner_code=partner,
                    is_active=True,
                )
            )
            counts["corridors"] += 1

    compliance = [
        ("BR", "BRL", "TX_SINGLE", 5000000, "Limite PIX sem KYC reforçado", "BACEN"),
        ("BR", "BRL", "TX_DAILY", 20000000, "Limite diário carteira", "BACEN"),
        ("US", "USD", "TX_SINGLE", 1000000, "CTR threshold reference", "FinCEN"),
        ("DE", "EUR", "KYC_THRESHOLD", 1000000, "AML harmonized", "EU-AMLD"),
        ("KE", "KES", "TX_SINGLE", 15000000, "M-Pesa daily cap ref", "CBK"),
    ]
    for country, ccy, ltype, amount, desc, ref in compliance:
        exists = (
            db.query(MoneyComplianceLimit)
            .filter(
                MoneyComplianceLimit.country_code == country,
                MoneyComplianceLimit.limit_type == ltype,
                MoneyComplianceLimit.currency_code == ccy,
            )
            .first()
        )
        if not exists:
            db.add(
                MoneyComplianceLimit(
                    id=new_id(),
                    country_code=country,
                    currency_code=ccy,
                    limit_type=ltype,
                    amount_cents=amount,
                    description=desc,
                    regulatory_ref=ref,
                    is_active=True,
                )
            )
            counts["compliance"] += 1

    from app.services.professional_service import seed_locker_players
    from app.services.advanced_seed import seed_payment_rails
    from app.services.intelligence_service import analyze_ecosystem, seed_intelligence_defaults

    player_counts = seed_locker_players(db)
    counts["payment_rails"] = seed_payment_rails(db)
    intel_seed = seed_intelligence_defaults(db)
    counts["fx_alert_rules"] = intel_seed.get("fx_rules", 0)
    counts["settlement_schedules"] = intel_seed.get("settlements", 0)
    counts["locker_players"] = player_counts.get("players", 0)
    counts["ecosystem_segments"] = player_counts.get("segments", 0)
    counts["player_relations"] = player_counts.get("relations", 0)
    counts["corridors"] = counts.get("corridors", 0) + player_counts.get("corridors", 0)
    counts["countries_updated"] = player_counts.get("countries_updated", 0)

    try:
        analyze_result = analyze_ecosystem(db, commit=False)
        counts["intelligence_analyze"] = analyze_result.model_dump()
    except Exception as exc:
        counts["intelligence_analyze_error"] = str(exc)

    db.commit()

    settings = get_settings()
    if settings.finance_admin_sync_after_seed and settings.finance_admin_sync_enabled:
        from app.services.finance_sync_service import sync_from_finance_admin

        try:
            sync_result = sync_from_finance_admin(db, trigger_finance_sync=True)
            counts["finance_sync"] = sync_result.model_dump()
        except Exception as exc:
            counts["finance_sync_error"] = str(exc)

    return counts

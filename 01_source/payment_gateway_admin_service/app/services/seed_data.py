from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.catalog import (
    LockerPaymentMethod,
    PaymentInterfaceCatalog,
    PaymentMethodCatalog,
    PaymentMethodUiAlias,
)
from app.models.gateway_ops import (
    PaymentGatewayDeviceRegistry,
    PaymentGatewayIdempotencyKey,
    PaymentGatewayRiskEvent,
)
from app.models.provider import PaymentProviderPartner
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def run_seed(db: Session) -> dict[str, int]:
    counts = {
        "methods": 0,
        "interfaces": 0,
        "aliases": 0,
        "locker_methods": 0,
        "providers": 0,
        "devices": 0,
        "idempotency": 0,
        "risk_events": 0,
    }
    now = _utcnow()
    epoch = int(time.time())

    if not db.query(PaymentMethodCatalog).filter(PaymentMethodCatalog.code == "PIX").first():
        db.add(
            PaymentMethodCatalog(
                code="PIX",
                name="PIX instantâneo",
                family="instant",
                is_instant=True,
                is_active=True,
                metadata_json={"provider_hint": "mercadopago"},
            )
        )
        counts["methods"] += 1

    if not db.query(PaymentMethodCatalog).filter(PaymentMethodCatalog.code == "CREDIT_CARD").first():
        db.add(
            PaymentMethodCatalog(
                code="CREDIT_CARD",
                name="Cartão de crédito",
                family="card",
                is_card=True,
                is_active=True,
            )
        )
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

    if not (
        db.query(LockerPaymentMethod)
        .filter(LockerPaymentMethod.locker_id == "LOCKER-DEMO-01", LockerPaymentMethod.method == "PIX")
        .first()
    ):
        db.add(
            LockerPaymentMethod(locker_id="LOCKER-DEMO-01", method="PIX", is_active=True)
        )
        counts["locker_methods"] += 1

    if not db.query(PaymentProviderPartner).filter(PaymentProviderPartner.code == "STRIPE-BR").first():
        db.add(
            PaymentProviderPartner(
                id="pg-stripe-br-001",
                name="Stripe Brasil",
                code="STRIPE-BR",
                provider_type="STRIPE",
                region_code="BR",
                api_base_url="https://api.stripe.com",
                credentials_secret_ref="vault/stripe/br",
                webhook_secret_ref="vault/stripe/br/webhook",
                active=True,
            )
        )
        counts["providers"] += 1

    if not db.query(PaymentProviderPartner).filter(PaymentProviderPartner.code == "MP-AR").first():
        db.add(
            PaymentProviderPartner(
                id="pg-mp-ar-001",
                name="Mercado Pago Argentina",
                code="MP-AR",
                provider_type="MERCADOPAGO",
                region_code="AR",
                api_base_url="https://api.mercadopago.com",
                credentials_secret_ref="vault/mp/ar",
                active=True,
            )
        )
        counts["providers"] += 1

    if not db.get(PaymentGatewayDeviceRegistry, "demo-device-hash-001"):
        db.add(
            PaymentGatewayDeviceRegistry(
                device_hash="demo-device-hash-001",
                version="1.0.0",
                first_seen_at_epoch=epoch - 3600,
                last_seen_at_epoch=epoch,
                seen_count=3,
                region_code="BR",
                locker_id="LOCKER-DEMO-01",
                flags_json={"trusted": True},
            )
        )
        counts["devices"] += 1

    if not db.get(PaymentGatewayIdempotencyKey, "idem-demo-001"):
        db.add(
            PaymentGatewayIdempotencyKey(
                id="idem-demo-001",
                endpoint="/gateway/payment/create",
                idem_key="order-demo-001",
                payload_hash="abc123",
                response_blob={"status": "ok"},
                status="COMPLETED",
                region_code="BR",
                sales_channel="TOTEM",
                created_at_epoch=epoch,
                expires_at_epoch=epoch + 86400,
            )
        )
        counts["idempotency"] += 1

    if not db.get(PaymentGatewayRiskEvent, "risk-demo-001"):
        db.add(
            PaymentGatewayRiskEvent(
                id="risk-demo-001",
                request_id=str(uuid.uuid4()),
                event_type="PAYMENT_ATTEMPT",
                decision="ALLOW",
                score=12,
                policy_id="default_v1",
                region_code="BR",
                locker_id="LOCKER-DEMO-01",
                slot=1,
                audit_event_id=str(uuid.uuid4()),
                reasons_json=[],
                signals_json={"velocity_ok": True},
                created_at_epoch=epoch,
            )
        )
        counts["risk_events"] += 1

    db.commit()
    return counts

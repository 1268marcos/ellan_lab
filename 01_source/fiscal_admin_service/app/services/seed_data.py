from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.data.fiscal_global_seed import FISCAL_ISSUERS_WORLD
from app.models.fiscal_admin import FiscalIssuerPartner
from app.models.fiscal_core import (
    FiscalAccountingApproval,
    FiscalAuthorityCallback,
    FiscalDocument,
    FiscalProviderHealthStatus,
    FiscalReconciliationGap,
    ProductFiscalConfig,
    TenantFiscalConfig,
)
from app.models.fiscal_global import FiscalAutoClassificationLog, FiscalWebhookDeliveryLog
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def run_seed(db: Session) -> dict[str, int]:
    counts = {
        "issuers": 0,
        "documents": 0,
        "gaps": 0,
        "health": 0,
        "tenants": 0,
        "products": 0,
        "approvals": 0,
        "callbacks": 0,
    }
    now = _utcnow()

    if not db.query(FiscalIssuerPartner).filter(FiscalIssuerPartner.code == "SEFAZ-BR-SP").first():
        db.add(
            FiscalIssuerPartner(
                id="fi-sefaz-br-sp",
                name="SEFAZ SP (NFC-e)",
                code="SEFAZ-BR-SP",
                issuer_type="SEFAZ",
                country="BR",
                region_code="SP",
                api_base_url="https://nfce.fazenda.sp.gov.br",
                active=True,
            )
        )
        counts["issuers"] += 1

    if not db.query(FiscalIssuerPartner).filter(FiscalIssuerPartner.code == "AT-PT").first():
        db.add(
            FiscalIssuerPartner(
                id="fi-at-pt",
                name="Autoridade Tributária PT (SAF-T)",
                code="AT-PT",
                issuer_type="AT_PT",
                country="PT",
                region_code="PT",
                api_base_url="https://faturas.portaldasfinancas.gov.pt",
                active=True,
            )
        )
        counts["issuers"] += 1

    for spec in FISCAL_ISSUERS_WORLD:
        if not db.query(FiscalIssuerPartner).filter(FiscalIssuerPartner.code == spec["code"]).first():
            db.add(FiscalIssuerPartner(**spec, active=True))
            counts["issuers"] += 1

    if not db.get(FiscalDocument, "fd-demo-001"):
        db.add(
            FiscalDocument(
                id="fd-demo-001",
                order_id="ORD-DEMO-FISCAL-01",
                receipt_code="NFC-20260523-0001",
                document_type="NFC_E_65",
                channel="LOCKER",
                region="BR",
                amount_cents=1590,
                currency="BRL",
                send_status="SENT",
                payload_json='{"serie":"1","numero":"42"}',
                issued_at=now,
                created_at=now,
                updated_at=now,
                tenant_id="tenant-magalu-demo",
            )
        )
        counts["documents"] += 1

    if not db.get(FiscalReconciliationGap, "gap-demo-001"):
        db.add(
            FiscalReconciliationGap(
                id="gap-demo-001",
                dedupe_key="order:ORD-DEMO-FISCAL-01:missing_invoice",
                gap_type="MISSING_B2B_INVOICE",
                severity="HIGH",
                status="OPEN",
                order_id="ORD-DEMO-FISCAL-01",
                details_json={"hint": "NF B2B pendente após NFC-e"},
                first_detected_at=now,
                last_detected_at=now,
            )
        )
        counts["gaps"] += 1

    if not db.get(FiscalProviderHealthStatus, "BR"):
        db.add(
            FiscalProviderHealthStatus(
                country="BR",
                provider_name="SEFAZ_STUB",
                mode="STUB",
                enabled=True,
                last_status="OK",
                last_http_status=200,
                last_latency_ms=45,
                checked_at=now,
            )
        )
        counts["health"] += 1

    if not db.get(TenantFiscalConfig, "tenant-magalu-demo"):
        db.add(
            TenantFiscalConfig(
                tenant_id="tenant-magalu-demo",
                cnpj="12.345.678/0001-90",
                razao_social="Magalu Lockers Demo LTDA",
                regime="SIMPLES",
                crt="1",
                cert_a1_ref="vault/a1/magalu-demo",
                is_active=True,
                created_at=now,
                brand_config={"company_name": "Magalu Lockers"},
            )
        )
        counts["tenants"] += 1

    if not db.get(ProductFiscalConfig, "SKU-LOCKER-RENT-01"):
        db.add(
            ProductFiscalConfig(
                sku_id="SKU-LOCKER-RENT-01",
                ncm_code="99880000",
                icms_cst="40",
                pis_cst="07",
                cofins_cst="07",
                cfop="5933",
                is_active=True,
            )
        )
        counts["products"] += 1

    if not db.get(FiscalAccountingApproval, "appr-demo-d13"):
        db.add(
            FiscalAccountingApproval(
                id="appr-demo-d13",
                owner="ops-fiscal@ellan.lab",
                status="IN_REVIEW",
                payload_json={"checklist": "D13", "done_items": 8, "total_items": 12},
            )
        )
        counts["approvals"] += 1

    if not db.get(FiscalAuthorityCallback, "cb-demo-001"):
        try:
            with db.begin_nested():
                db.add(
                    FiscalAuthorityCallback(
                        id="cb-demo-001",
                        invoice_id="INV-DEMO-001",
                        authority="SEFAZ",
                        event_type="AUTHORIZED",
                        status="OK",
                        protocol_number="PROT-20260523-ABC",
                        raw_payload={"cStat": "100"},
                        received_at=now,
                    )
                )
            counts["callbacks"] += 1
        except Exception:
            pass  # postgres_central: FK fiscal_authority_callbacks → invoices

    if not db.query(FiscalWebhookDeliveryLog).filter(FiscalWebhookDeliveryLog.id == "wh-dlq-demo-01").first():
        db.add(
            FiscalWebhookDeliveryLog(
                id="wh-dlq-demo-01",
                issuer_id="fi-sefaz-br-sp",
                event_type="fiscal.document.authorized",
                delivery_status="DLQ",
                http_status=502,
                attempt=5,
                error_message="upstream SEFAZ timeout",
            )
        )
        counts["webhook_dlq"] = 1

    if not db.query(FiscalAutoClassificationLog).filter(FiscalAutoClassificationLog.order_id == "ORD-DEMO-FISCAL-01").first():
        db.add(
            FiscalAutoClassificationLog(
                order_id="ORD-DEMO-FISCAL-01",
                invoice_id="INV-DEMO-001",
                sku_id="SKU-LOCKER-RENT-01",
                ncm_applied="99880000",
                icms_cst_applied="40",
                cfop_applied="5933",
                source="AUTO_PRODUCT_CONFIG",
            )
        )
        counts["classification_logs"] = 1

    db.commit()
    return counts

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.data.privacy_extended_seed import seed_privacy_extended
from app.data.privacy_regulations_catalog import PRIVACY_POLICIES_CATALOG, PRIVACY_REGULATIONS_CATALOG
from app.data.privacy_pro_seed import seed_privacy_pro
from app.data.privacy_player_legal_seed import seed_privacy_player_legal
from app.data.privacy_regulatory_seed import seed_privacy_regulatory
from app.services.privacy_ecosystem_service import seed_privacy_ecosystem
from app.models.privacy import (
    DataDeletionRequest,
    DataSubjectRequest,
    PrivacyConsent,
    PrivacyPolicyVersion,
    PrivacyRegulation,
    PrivacyWebhookEndpoint,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def run_seed(db: Session) -> dict[str, int]:
    counts = {
        "regulations": 0,
        "policies": 0,
        "consents": 0,
        "deletions": 0,
        "subject_requests": 0,
        "webhooks": 0,
    }
    now = _utcnow()

    for spec in PRIVACY_REGULATIONS_CATALOG:
        if not db.get(PrivacyRegulation, spec["id"]):
            db.add(
                PrivacyRegulation(
                    **spec,
                    active=True,
                    created_at=now,
                    updated_at=now,
                )
            )
            counts["regulations"] += 1

    for spec in PRIVACY_POLICIES_CATALOG:
        existing = db.get(PrivacyPolicyVersion, spec["id"])
        if not existing:
            db.add(
                PrivacyPolicyVersion(
                    **spec,
                    effective_at=now,
                    created_at=now,
                )
            )
            counts["policies"] += 1
        elif existing.content_url != spec.get("content_url"):
            existing.content_url = spec.get("content_url")
            existing.title = spec.get("title", existing.title)
            existing.summary = spec.get("summary", existing.summary)
            existing.version = spec.get("version", existing.version)

    consents = [
        {
            "id": "cons-gdpr-mkt-001",
            "regulation_code": "GDPR",
            "consent_type": "MARKETING",
            "granted": True,
            "user_id": "usr-demo-eu-001",
            "channel": "KIOSK",
            "policy_version": "3.0",
        },
        {
            "id": "cons-ukgdpr-mkt-001",
            "regulation_code": "UKGDPR",
            "consent_type": "MARKETING",
            "granted": True,
            "user_id": "usr-demo-uk-001",
            "channel": "WEB",
            "policy_version": "1.0",
        },
        {
            "id": "cons-lgpd-analytics-001",
            "regulation_code": "LGPD",
            "consent_type": "ANALYTICS",
            "granted": True,
            "guest_identifier": "guest-br-kiosk-42",
            "channel": "WEB",
            "policy_version": "2.1",
        },
        {
            "id": "cons-ccpa-optout-001",
            "regulation_code": "CCPA",
            "consent_type": "SALE_SHARE_OPT_OUT",
            "granted": False,
            "user_id": "usr-demo-us-001",
            "channel": "APP",
            "policy_version": "1.0",
        },
        {
            "id": "cons-pipeda-001",
            "regulation_code": "PIPEDA",
            "consent_type": "TELEMETRY",
            "granted": True,
            "user_id": "usr-demo-ca-001",
            "channel": "KIOSK",
            "policy_version": "1.0",
        },
        {
            "id": "cons-lgpd-correios-001",
            "regulation_code": "LGPD",
            "consent_type": "TELEMETRY",
            "granted": True,
            "user_id": "usr-demo-br-correios",
            "channel": "KIOSK",
            "policy_version": "2.1",
        },
        {
            "id": "cons-gdpr-ctt-001",
            "regulation_code": "GDPR",
            "consent_type": "MARKETING",
            "granted": True,
            "user_id": "usr-demo-pt-001",
            "channel": "WEB",
            "policy_version": "1.0",
        },
        {
            "id": "cons-appi-001",
            "regulation_code": "APPI",
            "consent_type": "ANALYTICS",
            "granted": True,
            "user_id": "usr-demo-jp-001",
            "channel": "APP",
            "policy_version": "1.0",
        },
    ]

    for spec in consents:
        if not db.get(PrivacyConsent, spec["id"]):
            db.add(
                PrivacyConsent(
                    **spec,
                    granted_at=now,
                    created_at=now,
                )
            )
            counts["consents"] += 1

    if not db.get(DataDeletionRequest, "del-req-demo-001"):
        db.add(
            DataDeletionRequest(
                id="del-req-demo-001",
                regulation_code="GDPR",
                user_id="usr-demo-eu-001",
                requested_by="usr-demo-eu-001",
                status="PENDING",
                reason="Account closure after last pickup at InPost locker",
                requested_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        counts["deletions"] += 1

    if not db.get(DataSubjectRequest, "dsar-lgpd-001"):
        db.add(
            DataSubjectRequest(
                id="dsar-lgpd-001",
                regulation_code="LGPD",
                user_id="usr-demo-br-001",
                request_type="ACCESS",
                status="PENDING",
                requested_by="usr-demo-br-001",
                details="Solicitação de cópia de dados de retirada Mercado Livre locker",
                due_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        counts["subject_requests"] += 1

    if not db.get(DataSubjectRequest, "dsar-pipeda-001"):
        db.add(
            DataSubjectRequest(
                id="dsar-pipeda-001",
                regulation_code="PIPEDA",
                user_id="usr-demo-ca-001",
                request_type="PORTABILITY",
                status="PENDING",
                requested_by="usr-demo-ca-001",
                details="Export pickup history — Canada cross-border locker",
                due_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        counts["subject_requests"] += 1

    webhooks = [
        {
            "id": "wh-gdpr-001",
            "regulation_code": "GDPR",
            "url": "https://hooks.ellanlab.example/privacy/gdpr",
            "events_json": '["consent.granted","consent.revoked","deletion.completed","dsar.completed"]',
        },
        {
            "id": "wh-lgpd-001",
            "regulation_code": "LGPD",
            "url": "https://hooks.ellanlab.example/privacy/lgpd",
            "events_json": '["consent.granted","dsar.access","deletion.completed"]',
        },
        {
            "id": "wh-ukgdpr-001",
            "regulation_code": "UKGDPR",
            "url": "https://hooks.ellanlab.example/privacy/uk",
            "events_json": '["consent.granted","deletion.completed"]',
        },
        {
            "id": "wh-pipeda-001",
            "regulation_code": "PIPEDA",
            "url": "https://hooks.ellanlab.example/privacy/ca",
            "events_json": '["dsar.completed","deletion.completed"]',
        },
        {
            "id": "wh-ccpa-001",
            "regulation_code": "CCPA",
            "url": "https://hooks.ellanlab.example/privacy/ccpa",
            "events_json": '["opt_out.recorded","consent.granted","consent.revoked","dsar.completed"]',
        },
    ]

    for spec in webhooks:
        if not db.get(PrivacyWebhookEndpoint, spec["id"]):
            db.add(
                PrivacyWebhookEndpoint(
                    **spec,
                    signing_algo="HMAC_SHA256",
                    active=True,
                    created_at=now,
                    updated_at=now,
                )
            )
            counts["webhooks"] += 1

    db.commit()
    ext = seed_privacy_extended(db)
    eco = seed_privacy_ecosystem(db)
    pro = seed_privacy_pro(db)
    reg = seed_privacy_regulatory(db)
    pld = seed_privacy_player_legal(db)
    return {**counts, **ext, **eco, **pro, **reg, **pld}

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.privacy_ecosystem import PrivacyEcosystemPlayer
from app.models.privacy_pro import PrivacyPlayerCertificationMirror
from app.services.crypto_util import new_id, utcnow

# Fallback seed when Partner Admin is offline (demo / CI)
_FALLBACK_CERTS: list[dict] = [
    {"player_code": "INPOST", "certification_type": "ISO27001", "status": "VALID", "issuer": "BSI", "source": "PARTNER"},
    {"player_code": "INPOST", "certification_type": "GDPR_DPA", "status": "VALID", "issuer": "InPost Legal", "source": "PARTNER"},
    {"player_code": "MELI", "certification_type": "LGPD_DPA", "status": "VALID", "issuer": "Mercado Livre", "source": "PARTNER"},
    {"player_code": "MELI", "certification_type": "SOC2", "status": "VALID", "issuer": "AICPA", "source": "PARTNER"},
    {"player_code": "AMAZON_HUB", "certification_type": "PCI_DSS", "status": "VALID", "issuer": "PCI SSC", "source": "PARTNER"},
    {"player_code": "CORREIOS", "certification_type": "LGPD_DPA", "status": "VALID", "issuer": "Correios", "source": "PARTNER"},
    {"player_code": "SHOPEE", "certification_type": "PDPA_SG", "status": "VALID", "issuer": "Shopee", "source": "MARKETPLACE"},
    {"player_code": "LAZADA", "certification_type": "ISO27001", "status": "VALID", "issuer": "Alibaba Cloud", "source": "MARKETPLACE"},
    {"player_code": "CAINIAO", "certification_type": "SOC2", "status": "VALID", "issuer": "Cainiao", "source": "PARTNER"},
    {"player_code": "YAMATO", "certification_type": "APPI_COMPLIANT", "status": "VALID", "issuer": "Yamato", "source": "PARTNER"},
]


def _mirror_out(row: PrivacyPlayerCertificationMirror) -> dict:
    return {
        "id": row.id,
        "player_code": row.player_code,
        "certification_type": row.certification_type,
        "status": row.status,
        "source": row.source,
        "external_id": row.external_id,
        "issuer": row.issuer,
        "evidence_url": row.evidence_url,
        "scope_notes": row.scope_notes,
        "synced_at": row.synced_at,
    }


def _fetch_partner_certifications(player_code: str | None = None) -> list[dict]:
    settings = get_settings()
    base = settings.partner_admin_base_url.rstrip("/")
    url = f"{base}/ecosystem/global-ops/certifications"
    if player_code:
        url += f"?player_code={player_code.upper()}"
    try:
        with httpx.Client(timeout=4.0) as client:
            resp = client.get(url)
        if resp.status_code != 200:
            return []
        data = resp.json()
        if isinstance(data, list):
            return data
        return data.get("items") or []
    except Exception:
        return []


def _fetch_partner_readiness(limit: int = 50) -> list[dict]:
    settings = get_settings()
    url = f"{settings.partner_admin_base_url.rstrip('/')}/ecosystem/global-ops/readiness?limit={limit}"
    try:
        with httpx.Client(timeout=4.0) as client:
            resp = client.get(url)
        if resp.status_code != 200:
            return []
        data = resp.json()
        return data if isinstance(data, list) else data.get("items") or []
    except Exception:
        return []


def _upsert_mirror(db: Session, cert: dict, *, source: str) -> None:
    player_code = (cert.get("player_code") or "").upper()
    cert_type = (cert.get("certification_type") or cert.get("type") or "UNKNOWN").upper()
    if not player_code:
        return
    ext_id = cert.get("id") or cert.get("external_id")
    existing = (
        db.query(PrivacyPlayerCertificationMirror)
        .filter_by(player_code=player_code, certification_type=cert_type, source=source)
        .first()
    )
    now = utcnow()
    if existing:
        existing.status = cert.get("status") or existing.status
        existing.external_id = ext_id or existing.external_id
        existing.issuer = cert.get("issuer") or existing.issuer
        existing.evidence_url = cert.get("evidence_url") or existing.evidence_url
        existing.scope_notes = cert.get("scope_notes") or existing.scope_notes
        existing.synced_at = now
    else:
        db.add(
            PrivacyPlayerCertificationMirror(
                id=new_id(),
                player_code=player_code,
                certification_type=cert_type,
                status=cert.get("status") or "VALID",
                source=source,
                external_id=ext_id,
                issuer=cert.get("issuer"),
                evidence_url=cert.get("evidence_url"),
                scope_notes=cert.get("scope_notes"),
                synced_at=now,
            )
        )


def sync_certifications_from_partner(db: Session, *, player_code: str | None = None) -> dict:
    remote = _fetch_partner_certifications(player_code)
    source_label = "PARTNER_LIVE" if remote else "FALLBACK"
    certs = remote if remote else [c for c in _FALLBACK_CERTS if not player_code or c["player_code"] == player_code.upper()]

    if not remote and not player_code:
        try:
            with httpx.Client(timeout=4.0) as client:
                client.post(f"{get_settings().partner_admin_base_url.rstrip('/')}/ecosystem/global-ops/seed")
                remote2 = _fetch_partner_certifications(None)
                if remote2:
                    certs = remote2
                    source_label = "PARTNER_LIVE"
        except Exception:
            pass

    for cert in certs:
        _upsert_mirror(db, cert, source=cert.get("source") or "PARTNER")
    db.commit()

    return {
        "synced": len(certs),
        "source": source_label,
        "player_code": player_code.upper() if player_code else None,
    }


def list_certification_mirrors(
    db: Session,
    *,
    player_code: str | None = None,
    limit: int = 200,
) -> list[dict]:
    q = db.query(PrivacyPlayerCertificationMirror)
    if player_code:
        q = q.filter(PrivacyPlayerCertificationMirror.player_code == player_code.upper())
    rows = q.order_by(PrivacyPlayerCertificationMirror.synced_at.desc()).limit(limit).all()
    return [_mirror_out(r) for r in rows]


def global_ops_bridge_summary(db: Session) -> dict:
    players = db.query(PrivacyEcosystemPlayer).filter(PrivacyEcosystemPlayer.active.is_(True)).count()
    certs = db.query(PrivacyPlayerCertificationMirror).count()
    valid = db.query(PrivacyPlayerCertificationMirror).filter(PrivacyPlayerCertificationMirror.status == "VALID").count()
    readiness = _fetch_partner_readiness(30)
    return {
        "privacy_ecosystem_players": players,
        "certifications_cached": certs,
        "certifications_valid": valid,
        "partner_readiness_rows": len(readiness),
        "readiness_preview": readiness[:5],
        "bridge_status": "LIVE" if readiness else "CACHE_ONLY",
    }

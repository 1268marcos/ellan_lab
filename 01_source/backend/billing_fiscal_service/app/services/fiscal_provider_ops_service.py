from __future__ import annotations

import time
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.fiscal_real_provider_client import RealProviderClientError, health_check
from app.models.fiscal_provider_health_status import FiscalProviderHealthStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _provider_config(country: str) -> dict:
    c = country.upper()
    if c == "BR":
        return {
            "country": "BR",
            "provider_name": "SVRS/SEFAZ",
            "enabled": bool(settings.fiscal_real_provider_br_enabled),
            "base_url": settings.fiscal_real_provider_base_url_br,
        }
    if c == "PT":
        return {
            "country": "PT",
            "provider_name": "AT Portugal",
            "enabled": bool(settings.fiscal_real_provider_pt_enabled),
            "base_url": settings.fiscal_real_provider_base_url_pt,
        }
    raise ValueError(f"country_not_supported: {country}")


def _derive_error_meta(err: str | None) -> dict:
    raw = str(err or "").strip()
    if not raw:
        return {
            "last_error_code": None,
            "last_error_retryable": None,
            "last_error_attempts": None,
        }
    code = raw.split(":", 1)[0].strip() if ":" in raw else raw
    retryable_match = re.search(r"retryable=(True|False)", raw)
    attempts_match = re.search(r"attempts=(\d+)", raw)
    retryable = None
    if retryable_match:
        retryable = retryable_match.group(1) == "True"
    attempts = int(attempts_match.group(1)) if attempts_match else None
    return {
        "last_error_code": code or None,
        "last_error_retryable": retryable,
        "last_error_attempts": attempts,
    }


def _upsert_health_row(db: Session, *, cfg: dict, status: str, http_status: int | None, latency_ms: int | None, err: str | None) -> FiscalProviderHealthStatus:
    row = db.query(FiscalProviderHealthStatus).filter(FiscalProviderHealthStatus.country == cfg["country"]).first()
    now = _utc_now()
    mode = "real" if cfg["enabled"] else "stub"
    if row is None:
        row = FiscalProviderHealthStatus(
            country=cfg["country"],
            provider_name=cfg["provider_name"],
            mode=mode,
            enabled=cfg["enabled"],
            base_url=cfg["base_url"],
            last_status=status,
            last_http_status=http_status,
            last_latency_ms=latency_ms,
            last_error=(err or None),
            checked_at=now,
        )
        db.add(row)
    else:
        row.provider_name = cfg["provider_name"]
        row.mode = mode
        row.enabled = cfg["enabled"]
        row.base_url = cfg["base_url"]
        row.last_status = status
        row.last_http_status = http_status
        row.last_latency_ms = latency_ms
        row.last_error = (err or None)
        row.checked_at = now
    db.commit()
    db.refresh(row)
    return row


def test_provider_connectivity(db: Session, *, country: str) -> dict:
    cfg = _provider_config(country)
    if not cfg["enabled"]:
        row = _upsert_health_row(
            db,
            cfg=cfg,
            status="SKIPPED",
            http_status=None,
            latency_ms=None,
            err="provider_real_disabled",
        )
        return _row_to_dict(row)
    if not cfg["base_url"]:
        row = _upsert_health_row(
            db,
            cfg=cfg,
            status="ERROR",
            http_status=None,
            latency_ms=None,
            err="provider_base_url_missing",
        )
        return _row_to_dict(row)

    t0 = time.perf_counter()
    try:
        http_status, body = health_check(cfg["country"])
        latency_ms = int((time.perf_counter() - t0) * 1000)
        row = _upsert_health_row(
            db,
            cfg=cfg,
            status="OK",
            http_status=http_status,
            latency_ms=latency_ms,
            err=None,
        )
        out = _row_to_dict(row)
        out["health_payload"] = body
        return out
    except RealProviderClientError as exc:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        row = _upsert_health_row(
            db,
            cfg=cfg,
            status="ERROR",
            http_status=None,
            latency_ms=latency_ms,
            err=str(exc)[:1000],
        )
        out = _row_to_dict(row)
        out["last_error_code"] = exc.code
        out["last_error_retryable"] = exc.retryable
        out["last_error_attempts"] = exc.attempts
        return out


def list_provider_status(db: Session) -> list[dict]:
    countries = ["BR", "PT"]
    out: list[dict] = []
    for c in countries:
        cfg = _provider_config(c)
        row = db.query(FiscalProviderHealthStatus).filter(FiscalProviderHealthStatus.country == c).first()
        if row is None:
            out.append(
                {
                    **cfg,
                    "mode": "real" if cfg["enabled"] else "stub",
                    "last_status": "NEVER_TESTED",
                    "last_http_status": None,
                    "last_latency_ms": None,
                    "last_error": None,
                    "checked_at": None,
                }
            )
            continue
        out.append(_row_to_dict(row))
    return out


def _row_to_dict(row: FiscalProviderHealthStatus) -> dict:
    error_meta = _derive_error_meta(row.last_error)
    return {
        "country": row.country,
        "provider_name": row.provider_name,
        "mode": row.mode,
        "enabled": bool(row.enabled),
        "base_url": row.base_url,
        "last_status": row.last_status,
        "last_http_status": row.last_http_status,
        "last_latency_ms": row.last_latency_ms,
        "last_error": row.last_error,
        "last_error_code": error_meta["last_error_code"],
        "last_error_retryable": error_meta["last_error_retryable"],
        "last_error_attempts": error_meta["last_error_attempts"],
        "checked_at": row.checked_at.isoformat() if row.checked_at else None,
    }

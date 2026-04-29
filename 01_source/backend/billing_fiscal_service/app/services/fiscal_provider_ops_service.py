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


def build_br_go_no_go_checklist(db: Session, *, run_connectivity: bool = False) -> dict:
    if run_connectivity:
        br = test_provider_connectivity(db, country="BR")
    else:
        br = next((x for x in list_provider_status(db) if x.get("country") == "BR"), None)
        if br is None:
            br = {
                "country": "BR",
                "enabled": bool(settings.fiscal_real_provider_br_enabled),
                "base_url": settings.fiscal_real_provider_base_url_br,
                "last_status": "NEVER_TESTED",
                "last_http_status": None,
                "last_latency_ms": None,
                "last_error_code": None,
            }

    checks = [
        {
            "id": "flag_enabled",
            "label": "Flag BR real habilitada",
            "ok": bool(br.get("enabled")),
            "detail": "FISCAL_REAL_PROVIDER_BR_ENABLED deve estar true para go-live real.",
        },
        {
            "id": "base_url_present",
            "label": "Base URL BR configurada",
            "ok": bool(br.get("base_url")),
            "detail": "FISCAL_REAL_PROVIDER_BASE_URL_BR deve estar preenchida.",
        },
        {
            "id": "last_status_ok",
            "label": "Última conectividade OK",
            "ok": str(br.get("last_status") or "").upper() == "OK",
            "detail": "Executar teste BR no OPS; status esperado: OK.",
        },
        {
            "id": "latency_safe",
            "label": "Latência em faixa segura",
            "ok": (br.get("last_latency_ms") is not None) and int(br.get("last_latency_ms") or 0) < 1500,
            "detail": "Latência recomendada < 1500ms para iniciar real com segurança.",
        },
    ]
    all_ok = all(bool(c["ok"]) for c in checks)
    return {
        "country": "BR",
        "go_no_go": "GO" if all_ok else "NO_GO",
        "summary": (
            "Checklist BR apto para início controlado do provider real."
            if all_ok
            else "Checklist BR incompleto. Manter trilha A (stub-ready) até resolver pendências."
        ),
        "run_connectivity": bool(run_connectivity),
        "checked_at": _utc_now().isoformat(),
        "provider_snapshot": br,
        "checks": checks,
        "next_actions": [
            "Se NO_GO: corrigir itens pendentes e repetir go/no-go.",
            "Se GO: habilitar rollout controlado com monitoramento reforçado no ops/fiscal/providers.",
            "Se degradação após GO: rollback imediato via flag BR real=false e restart fiscal.",
        ],
    }


def build_pt_go_no_go_checklist(db: Session, *, run_connectivity: bool = False) -> dict:
    if run_connectivity:
        pt = test_provider_connectivity(db, country="PT")
    else:
        pt = next((x for x in list_provider_status(db) if x.get("country") == "PT"), None)
        if pt is None:
            pt = {
                "country": "PT",
                "enabled": bool(settings.fiscal_real_provider_pt_enabled),
                "base_url": settings.fiscal_real_provider_base_url_pt,
                "last_status": "NEVER_TESTED",
                "last_http_status": None,
                "last_latency_ms": None,
                "last_error_code": None,
            }

    checks = [
        {
            "id": "flag_enabled",
            "label": "Flag PT real habilitada",
            "ok": bool(pt.get("enabled")),
            "detail": "FISCAL_REAL_PROVIDER_PT_ENABLED deve estar true para go-live real.",
        },
        {
            "id": "base_url_present",
            "label": "Base URL PT configurada",
            "ok": bool(pt.get("base_url")),
            "detail": "FISCAL_REAL_PROVIDER_BASE_URL_PT deve estar preenchida.",
        },
        {
            "id": "last_status_ok",
            "label": "Última conectividade OK",
            "ok": str(pt.get("last_status") or "").upper() == "OK",
            "detail": "Executar teste PT no OPS; status esperado: OK.",
        },
        {
            "id": "latency_safe",
            "label": "Latência em faixa segura",
            "ok": (pt.get("last_latency_ms") is not None) and int(pt.get("last_latency_ms") or 0) < 1500,
            "detail": "Latência recomendada < 1500ms para iniciar real com segurança.",
        },
    ]
    all_ok = all(bool(c["ok"]) for c in checks)
    return {
        "country": "PT",
        "go_no_go": "GO" if all_ok else "NO_GO",
        "summary": (
            "Checklist PT apto para início controlado do provider real."
            if all_ok
            else "Checklist PT incompleto. Manter trilha A (stub-ready) até resolver pendências."
        ),
        "run_connectivity": bool(run_connectivity),
        "checked_at": _utc_now().isoformat(),
        "provider_snapshot": pt,
        "checks": checks,
        "next_actions": [
            "Se NO_GO: corrigir itens pendentes e repetir go/no-go.",
            "Se GO: habilitar rollout controlado com monitoramento reforçado no ops/fiscal/providers.",
            "Se degradação após GO: rollback imediato via flag PT real=false e restart fiscal.",
        ],
    }


def _row_to_dict(row: FiscalProviderHealthStatus) -> dict:
    error_meta = _derive_error_meta(row.last_error)
    action = _derive_action_plan(
        country=row.country,
        enabled=bool(row.enabled),
        last_status=row.last_status,
        last_http_status=row.last_http_status,
        last_latency_ms=row.last_latency_ms,
        last_error_code=error_meta["last_error_code"],
        last_error_retryable=error_meta["last_error_retryable"],
    )
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
        "action_required": action["action_required"],
        "action_severity": action["severity"],
        "action_summary": action["summary"],
        "action_steps": action["steps"],
        "rollback_checklist": _rollback_checklist_for_country(row.country),
        "checked_at": row.checked_at.isoformat() if row.checked_at else None,
    }


def _derive_action_plan(
    *,
    country: str,
    enabled: bool,
    last_status: str | None,
    last_http_status: int | None,
    last_latency_ms: int | None,
    last_error_code: str | None,
    last_error_retryable: bool | None,
) -> dict:
    status = str(last_status or "").upper()
    if not enabled:
        return {
            "action_required": False,
            "severity": "INFO",
            "summary": f"{country}: provider real desabilitado. Operar em stub monitorado.",
            "steps": [
                "Validar se o uso de STUB foi decisão aprovada para a janela atual.",
                "Monitorar fila fiscal e reconciliação; sem ação de rollback necessária.",
            ],
        }

    if status in {"NEVER_TESTED", "SKIPPED"}:
        return {
            "action_required": True,
            "severity": "WARN",
            "summary": f"{country}: executar teste de conectividade antes de liberar tráfego operacional.",
            "steps": [
                "Executar Testar país na tela OPS.",
                "Se continuar sem resposta, revisar token/URL e iniciar fallback controlado.",
            ],
        }

    if status == "ERROR":
        severity = "CRITICAL" if (last_error_retryable is False or last_http_status in {401, 403, 422}) else "HIGH"
        summary = f"{country}: erro no provider real detectado. Preparar fallback e avaliar rollback."
        steps = [
            "Executar reteste imediato de conectividade para confirmar estado.",
            "Se erro persistir, operar fallback (stub) e congelar mudanças de configuração.",
            "Aplicar checklist de rollback do país antes de nova tentativa de retorno ao real.",
        ]
        if last_error_code:
            steps.insert(1, f"Classificar incidente pelo código canônico: {last_error_code}.")
        return {
            "action_required": True,
            "severity": severity,
            "summary": summary,
            "steps": steps,
        }

    if (last_latency_ms or 0) >= 1500:
        return {
            "action_required": True,
            "severity": "HIGH",
            "summary": f"{country}: latência elevada no provider real (>=1500ms).",
            "steps": [
                "Repetir teste para validar se é pico transitório.",
                "Se recorrente, reduzir operações sensíveis e preparar fallback preventivo.",
            ],
        }

    return {
        "action_required": False,
        "severity": "OK",
        "summary": f"{country}: operação estável no provider real.",
        "steps": [
            "Manter monitoramento contínuo e testes periódicos.",
        ],
    }


def _rollback_checklist_for_country(country: str) -> list[str]:
    c = str(country or "").upper()
    base = [
        "Congelar deploy e mudanças de configuração fiscal.",
        "Registrar incidente com janela, impacto e evidências (status/erro/latência).",
        "Confirmar processamento em fallback antes de reabrir tráfego real.",
    ]
    if c == "BR":
        return [
            *base,
            "BR: validar emissões NFC-e via SVRS stub assíncrono (receipt/protocol).",
            "BR: conferir metadados provider_adapter/fallback_reason em government_response.raw.",
            "BR: executar smoke reprocess por order_id e validar reconciliação.",
        ]
    if c == "PT":
        return [
            *base,
            "PT: validar emissão/cancelamento no stub dedicado AT com contrato canônico.",
            "PT: conferir provider_adapter/fallback_reason em government_response.raw.",
            "PT: verificar fila de documentos e consistência antes de retorno ao real.",
        ]
    return base

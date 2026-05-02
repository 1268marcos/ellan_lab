"""P0 Fiscal ELLAN LAB — matriz canónica país × tenant de emissores (governança + overlay de runtime)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.services.fiscal_provider_ops_service import list_provider_status

SCOPE_FISCAL_ISSUER_GOVERNANCE_MATRIX = "SPRINT2_FISCAL_ISSUER_GOVERNANCE_MATRIX"

# Linhas canónicas: autoridade, perfil de emissor, modos permitidos e política de fallback auditável.
_ISSUER_MATRIX_SEED: tuple[dict, ...] = (
    {
        "tenant_id": "*",
        "tenant_label": "DEFAULT_ELLAN_LAB",
        "country": "BR",
        "fiscal_authority": "SEFAZ/SVRS",
        "issuer_profile": "LOCKER_NFCE_BR_MAIN",
        "document_family": "NFC-e / NF-e",
        "allowed_modes": ("stub", "real", "hybrid"),
        "fallback_policy": "stub_when_real_disabled_or_error",
        "change_control_owner": "fiscal-ops-br",
        "audit_channel": "fiscal/management-daily",
    },
    {
        "tenant_id": "*",
        "tenant_label": "DEFAULT_ELLAN_LAB",
        "country": "PT",
        "fiscal_authority": "AT Portugal",
        "issuer_profile": "ATCUD_SAFT_PT_MAIN",
        "document_family": "SAFT-PT / ATCUD",
        "allowed_modes": ("stub", "real", "hybrid"),
        "fallback_policy": "stub_when_real_disabled_or_error",
        "change_control_owner": "fiscal-ops-pt",
        "audit_channel": "fiscal/management-daily",
    },
    {
        "tenant_id": "tenant_br_isolated_pool",
        "tenant_label": "POOL_ISOLADO_BR",
        "country": "BR",
        "fiscal_authority": "SEFAZ/SVRS",
        "issuer_profile": "LOCKER_NFCE_BR_ISOLATED",
        "document_family": "NFC-e / NF-e",
        "allowed_modes": ("stub", "hybrid"),
        "fallback_policy": "hybrid_requires_dual_approval",
        "change_control_owner": "fiscal-ops-br",
        "audit_channel": "ops/fiscal/providers",
    },
)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_fiscal_issuer_governance_matrix(db: Session) -> dict:
    providers = {str(p.get("country") or "").upper(): p for p in list_provider_status(db)}
    rows: list[dict] = []
    for seed in _ISSUER_MATRIX_SEED:
        c = str(seed["country"]).upper()
        overlay = providers.get(c) or {}
        effective_mode = str(overlay.get("mode") or ("real" if overlay.get("enabled") else "stub"))
        rows.append(
            {
                **seed,
                "allowed_modes": list(seed["allowed_modes"]),
                "provider_runtime": {
                    "enabled": bool(overlay.get("enabled")),
                    "mode": overlay.get("mode"),
                    "last_status": overlay.get("last_status"),
                    "last_latency_ms": overlay.get("last_latency_ms"),
                    "checked_at": overlay.get("checked_at"),
                },
                "effective_mode": effective_mode,
                "matrix_row_ok": bool(seed.get("fiscal_authority") and seed.get("issuer_profile") and effective_mode),
            }
        )

    matrix_row_ok_count = sum(1 for r in rows if r.get("matrix_row_ok"))
    summary = {
        "matrix_rows": len(rows),
        "matrix_rows_ok": matrix_row_ok_count,
        "countries_distinct": sorted({str(r["country"]).upper() for r in rows}),
        "tenants_distinct": sorted({str(r["tenant_id"]) for r in rows}),
        "governance_complete": matrix_row_ok_count == len(rows) and len(rows) > 0,
    }

    return {
        "scope": SCOPE_FISCAL_ISSUER_GOVERNANCE_MATRIX,
        "generated_at": _utc_iso(),
        "summary": summary,
        "matrix": rows,
    }

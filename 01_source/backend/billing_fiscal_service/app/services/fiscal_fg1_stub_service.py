from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


FG1_WAVE_COUNTRIES = ("US", "AU", "PL", "CA", "FR")
FG1_OPERATIONS = ("authorize", "cancel", "correct", "status")

_SCENARIO_ROWS = (
    ("AUTHORIZE_SUCCESS", "authorize", "SUCCESS", "AUTORIZADO"),
    ("AUTHORIZE_REJECTED", "authorize", "BUSINESS_REJECTED", "REJEITADO"),
    ("AUTHORIZE_SCHEMA_ERROR", "authorize", "VALIDATION_ERROR", "ERRO_VALIDACAO"),
    ("AUTHORIZE_TIMEOUT", "authorize", "TIMEOUT", "TIMEOUT"),
    ("CANCEL_SUCCESS", "cancel", "SUCCESS", "CANCELADO"),
    ("CANCEL_DEADLINE_EXPIRED", "cancel", "BUSINESS_REJECTED", "PRAZO_EXPIRADO"),
    ("CORRECT_SUCCESS", "correct", "SUCCESS", "CARTA_CORRECAO_APLICADA"),
    ("STATUS_AUTHORIZED", "status", "AUTHORIZED", "AUTORIZADO"),
    ("STATUS_NOT_FOUND", "status", "NOT_FOUND", "NAO_ENCONTRADO"),
)

_ADAPTER_BY_COUNTRY = {
    "US": "irs_mef_stub_adapter_v1",
    "AU": "ato_stub_adapter_v1",
    "PL": "ksef_stub_adapter_v1",
    "CA": "cra_stub_adapter_v1",
    "FR": "chorus_stub_adapter_v1",
}

_AUTHORITY_BY_COUNTRY = {
    "US": "IRS",
    "AU": "ATO",
    "PL": "KSeF",
    "CA": "CRA",
    "FR": "DGFiP",
}

_REGION_BY_COUNTRY = {
    "US": "NA",
    "AU": "OCEANIA",
    "PL": "EU",
    "CA": "NA",
    "FR": "EU",
}

_ALLOWED_REGIONS_BY_COUNTRY = {
    "US": ("NA", "US-CA", "US-TX", "US-NY"),
    "AU": ("OCEANIA",),
    "PL": ("EU",),
    "CA": ("NA", "CA-QC"),
    "FR": ("EU",),
}

_FIXTURE_REQUIRED_FIELDS = (
    "fixture_version",
    "country_code",
    "operation",
    "scenario",
    "adapter_name",
    "authority",
    "region",
    "canonical_status",
    "authority_status",
    "fixture_relative_path",
)


def _scenario_map() -> dict[str, dict]:
    return {
        code: {
            "scenario": code,
            "operation": operation,
            "canonical_status": canonical_status,
            "authority_status": authority_status,
        }
        for code, operation, canonical_status, authority_status in _SCENARIO_ROWS
    }


def _default_scenario_for_operation(operation: str) -> str:
    op = str(operation or "").strip().lower()
    defaults = {
        "authorize": "AUTHORIZE_SUCCESS",
        "cancel": "CANCEL_SUCCESS",
        "correct": "CORRECT_SUCCESS",
        "status": "STATUS_AUTHORIZED",
    }
    return defaults.get(op, "AUTHORIZE_SUCCESS")


def _fixture_payload(country: str, operation: str, scenario_code: str) -> dict:
    return {
        "fixture_version": "fg1-fixtures-v1",
        "country_code": country,
        "operation": operation,
        "scenario": scenario_code,
        "document_reference": f"{country}-{operation}-DOC-001",
        "order_reference": f"{country}-{operation}-ORDER-001",
        "amount_cents": 12345,
        "currency": "LOCAL",
        "customer_tax_id": "TAX-STUB-001",
    }


def _validate_country(country: str) -> str:
    normalized = str(country or "").strip().upper()
    if normalized not in FG1_WAVE_COUNTRIES:
        raise ValueError(f"country must be one of: {', '.join(FG1_WAVE_COUNTRIES)}")
    return normalized


def _validate_operation(operation: str) -> str:
    normalized = str(operation or "").strip().lower()
    if normalized not in FG1_OPERATIONS:
        raise ValueError(f"operation must be one of: {', '.join(FG1_OPERATIONS)}")
    return normalized


def _resolve_region(country: str, region: str | None = None) -> str:
    normalized_country = _validate_country(country)
    default_region = _REGION_BY_COUNTRY.get(normalized_country, "GLOBAL")
    candidate = str(region or "").strip().upper()
    if not candidate:
        return default_region
    allowed = _ALLOWED_REGIONS_BY_COUNTRY.get(normalized_country, (default_region,))
    if candidate not in allowed:
        allowed_str = ", ".join(allowed)
        raise ValueError(f"region must be one of: {allowed_str}")
    return candidate


def fg1_fixtures_root() -> Path:
    """Raiz do serviço billing_fiscal_service: .../fixtures/fiscal/fg1."""
    return Path(__file__).resolve().parents[2] / "fixtures" / "fiscal" / "fg1"


def fg1_fixture_absolute_path(country: str, operation: str, scenario_code: str) -> Path:
    return fg1_fixtures_root() / country.lower() / operation / f"{scenario_code.lower()}.json"


def build_fg1_fixture_document(country: str, operation: str, scenario_code: str) -> dict:
    """Documento canônico persistido em disco (mesmo contrato usado pelo simulate quando arquivo ausente)."""
    normalized_country = _validate_country(country)
    normalized_operation = _validate_operation(operation)
    scen = str(scenario_code or "").strip().upper()
    scenarios = _scenario_map()
    if scen not in scenarios:
        raise ValueError("scenario is invalid for FG-1 scenario matrix")
    row = scenarios[scen]
    if row["operation"] != normalized_operation:
        raise ValueError("scenario does not belong to provided operation")
    base = _fixture_payload(normalized_country, normalized_operation, scen)
    return {
        **base,
        "adapter_name": _ADAPTER_BY_COUNTRY[normalized_country],
        "authority": _AUTHORITY_BY_COUNTRY.get(normalized_country, normalized_country),
        "region": _resolve_region(normalized_country),
        "canonical_status": row["canonical_status"],
        "authority_status": row["authority_status"],
        "fixture_relative_path": (
            f"fixtures/fiscal/fg1/{normalized_country.lower()}/{normalized_operation}/{scen.lower()}.json"
        ),
    }


def read_fg1_fixture_document(country: str, operation: str, scenario: str | None = None) -> dict:
    normalized_country = _validate_country(country)
    normalized_operation = _validate_operation(operation)
    scenario_code = str(scenario or "").strip().upper() or _default_scenario_for_operation(normalized_operation)
    path = fg1_fixture_absolute_path(normalized_country, normalized_operation, scenario_code)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return build_fg1_fixture_document(normalized_country, normalized_operation, scenario_code)


def fg1_fixture_source(country: str, operation: str, scenario: str | None = None) -> str:
    normalized_country = _validate_country(country)
    normalized_operation = _validate_operation(operation)
    scenario_code = str(scenario or "").strip().upper() or _default_scenario_for_operation(normalized_operation)
    return "disk" if fg1_fixture_absolute_path(normalized_country, normalized_operation, scenario_code).is_file() else "synthetic"


def build_fg1_fixture_inventory() -> dict:
    root = fg1_fixtures_root()
    expected = len(_scenario_map()) * len(FG1_WAVE_COUNTRIES)
    if not root.exists():
        return {
            "wave": "FG-1-WAVE-1",
            "inventory_version": "fg1-fixture-inventory-v1",
            "fixture_root": "fixtures/fiscal/fg1",
            "absolute_path": str(root),
            "exists": False,
            "count": 0,
            "expected_count": expected,
            "complete": False,
            "files": [],
        }
    files = []
    for path in sorted(root.rglob("*.json")):
        rel = path.relative_to(root).as_posix()
        files.append({"relative_path": rel, "bytes": path.stat().st_size})
    return {
        "wave": "FG-1-WAVE-1",
        "inventory_version": "fg1-fixture-inventory-v1",
        "fixture_root": "fixtures/fiscal/fg1",
        "absolute_path": str(root),
        "exists": True,
        "count": len(files),
        "expected_count": expected,
        "complete": len(files) == expected,
        "files": files,
    }


def build_fg1_stub_adapters_catalog() -> dict:
    items = []
    for country in FG1_WAVE_COUNTRIES:
        adapter = _ADAPTER_BY_COUNTRY[country]
        items.append(
            {
                "country_code": country,
                "adapter_name": adapter,
                "stub_mode": True,
                "operations_supported": list(FG1_OPERATIONS),
                "scenario_count": len(_SCENARIO_ROWS),
                "telemetry_fields": [
                    "provider_adapter",
                    "region",
                    "scenario",
                    "canonical_status",
                    "authority_status",
                    "operation",
                    "country_code",
                    "trace_id",
                    "fixture_source",
                ],
            }
        )
    return {
        "wave": "FG-1-WAVE-1",
        "catalog_version": "fg1-stub-adapters-v1",
        "items": items,
        "count": len(items),
    }


def build_fg1_fixtures_matrix() -> dict:
    scenarios = _scenario_map()
    rows = []
    for country in FG1_WAVE_COUNTRIES:
        for scenario_code, scenario in scenarios.items():
            rows.append(
                {
                    "country_code": country,
                    "adapter_name": _ADAPTER_BY_COUNTRY[country],
                    "operation": scenario["operation"],
                    "scenario": scenario_code,
                    "canonical_status": scenario["canonical_status"],
                    "authority_status": scenario["authority_status"],
                    "fixture_path": f"fixtures/fiscal/fg1/{country.lower()}/{scenario['operation']}/{scenario_code.lower()}.json",
                }
            )
    return {
        "wave": "FG-1-WAVE-1",
        "matrix_version": "fg1-fixtures-v1",
        "rows": rows,
        "count": len(rows),
    }


def build_fg1_coverage_gate() -> dict:
    scenarios = _scenario_map()
    required_operations = list(FG1_OPERATIONS)
    required_scenarios_by_operation: dict[str, list[str]] = {}
    for operation in required_operations:
        required_scenarios_by_operation[operation] = sorted(
            [code for code, row in scenarios.items() if row["operation"] == operation]
        )

    fixtures = build_fg1_fixtures_matrix()
    coverage_rows = fixtures["rows"]
    countries = []
    missing_total = 0
    for country in FG1_WAVE_COUNTRIES:
        country_rows = [row for row in coverage_rows if row["country_code"] == country]
        present_by_operation: dict[str, set[str]] = {}
        for row in country_rows:
            operation = str(row.get("operation") or "").lower()
            scenario = str(row.get("scenario") or "").upper()
            present_by_operation.setdefault(operation, set()).add(scenario)

        operation_items = []
        country_missing = 0
        for operation in required_operations:
            required_scenarios = required_scenarios_by_operation.get(operation, [])
            present = sorted(present_by_operation.get(operation, set()))
            missing = sorted([scenario for scenario in required_scenarios if scenario not in set(present)])
            country_missing += len(missing)
            operation_items.append(
                {
                    "operation": operation,
                    "required_scenarios": required_scenarios,
                    "present_scenarios": present,
                    "missing_scenarios": missing,
                    "coverage_status": "OK" if len(missing) == 0 else "MISSING",
                }
            )

        missing_total += country_missing
        countries.append(
            {
                "country_code": country,
                "adapter_name": _ADAPTER_BY_COUNTRY[country],
                "missing_scenarios_count": country_missing,
                "coverage_status": "GO" if country_missing == 0 else "NO_GO",
                "operations": operation_items,
            }
        )

    return {
        "wave": "FG-1-WAVE-1",
        "gate_version": "fg1-coverage-gate-v1",
        "required_operations": required_operations,
        "required_scenarios_total": len(scenarios),
        "country_count": len(countries),
        "missing_scenarios_total": missing_total,
        "decision": "GO" if missing_total == 0 else "NO_GO",
        "countries": countries,
    }


def build_fg1_stub_wave_readiness() -> dict:
    """Checkpoint executivo de prontidão stub da onda FG-1 (G+3)."""
    fixtures = build_fg1_fixtures_matrix()
    inventory = build_fg1_fixture_inventory()
    envelope = validate_fg1_envelope_contract()
    error_statuses_required = {"TIMEOUT", "BUSINESS_REJECTED", "NOT_FOUND"}
    rows = fixtures.get("rows") or []

    scenario_statuses: dict[str, set[str]] = {}
    for row in rows:
        country = str(row.get("country_code") or "").upper()
        if not country:
            continue
        status = str(row.get("canonical_status") or "").upper()
        if not status:
            continue
        scenario_statuses.setdefault(country, set()).add(status)

    countries = []
    countries_not_ready = 0
    for country in FG1_WAVE_COUNTRIES:
        statuses = scenario_statuses.get(country, set())
        missing_error_statuses = sorted(error_statuses_required - statuses)
        ready = len(missing_error_statuses) == 0
        if not ready:
            countries_not_ready += 1
        countries.append(
            {
                "country_code": country,
                "stub_adapter": _ADAPTER_BY_COUNTRY.get(country),
                "missing_error_statuses": missing_error_statuses,
                "status": "READY" if ready else "MISSING_ERROR_SCENARIOS",
            }
        )

    checks = [
        {
            "name": "fixture_inventory_complete",
            "status": "PASS" if bool(inventory.get("complete")) else "FAIL",
            "details": {
                "count": int(inventory.get("count") or 0),
                "expected_count": int(inventory.get("expected_count") or 0),
            },
        },
        {
            "name": "envelope_contract_ok",
            "status": "PASS" if str(envelope.get("status") or "").upper() == "OK" else "FAIL",
            "details": {
                "error_count": int(envelope.get("error_count") or 0),
                "checked_pairs": int(envelope.get("checked_pairs") or 0),
            },
        },
        {
            "name": "required_error_scenarios_by_country",
            "status": "PASS" if countries_not_ready == 0 else "FAIL",
            "details": {
                "countries_not_ready": countries_not_ready,
            },
        },
    ]
    decision = "GO" if all(str(c.get("status") or "").upper() == "PASS" for c in checks) else "NO_GO"
    return {
        "wave": "FG-1-WAVE-1",
        "readiness_version": "fg1-stub-wave-readiness-v1",
        "decision": decision,
        "checks": checks,
        "countries": countries,
        "country_count": len(countries),
        "countries_not_ready": countries_not_ready,
    }


def simulate_fg1_stub(country: str, operation: str, scenario: str | None = None, region: str | None = None) -> dict:
    normalized_country = _validate_country(country)
    normalized_operation = _validate_operation(operation)
    scenario_code = str(scenario or "").strip().upper() or _default_scenario_for_operation(normalized_operation)

    scenarios = _scenario_map()
    if scenario_code not in scenarios:
        raise ValueError("scenario is invalid for FG-1 scenario matrix")
    scenario_row = scenarios[scenario_code]
    if scenario_row["operation"] != normalized_operation:
        raise ValueError("scenario does not belong to provided operation")

    trace_id = f"fg1stub-{normalized_country.lower()}-{normalized_operation}-{int(datetime.now(timezone.utc).timestamp())}"
    fixture = read_fg1_fixture_document(normalized_country, normalized_operation, scenario_code)
    fixture_source = fg1_fixture_source(normalized_country, normalized_operation, scenario_code)
    provider_adapter = _ADAPTER_BY_COUNTRY[normalized_country]
    resolved_region = _resolve_region(normalized_country, region)
    response = {
        "wave": "FG-1-WAVE-1",
        "mode": "stub",
        "country_code": normalized_country,
        "operation": normalized_operation,
        "scenario": scenario_code,
        "canonical_status": scenario_row["canonical_status"],
        "authority_status": scenario_row["authority_status"],
        "telemetry": {
            "trace_id": trace_id,
            "provider_adapter": provider_adapter,
            "region": resolved_region,
            "fixture_source": fixture_source,
            "event_name": "fiscal_fg1_stub_simulated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "government_response": {
            "status": scenario_row["canonical_status"],
            "raw": {
                "provider_adapter": provider_adapter,
                "scenario": scenario_code,
                "operation": normalized_operation,
                "authority_status": scenario_row["authority_status"],
                "country_code": normalized_country,
                "region": resolved_region,
                "trace_id": trace_id,
            },
        },
        "fixture": fixture,
    }
    logger.info(
        "fiscal_fg1_stub_simulated",
        extra={
            "trace_id": trace_id,
            "country_code": normalized_country,
            "operation": normalized_operation,
            "scenario": scenario_code,
            "provider_adapter": provider_adapter,
            "region": resolved_region,
            "fixture_source": fixture_source,
            "canonical_status": scenario_row["canonical_status"],
        },
    )
    return response


def validate_fg1_envelope_contract() -> dict:
    """Valida consistência mínima do envelope fixture/simulate para a onda FG-1."""
    scenarios = _scenario_map()
    errors: list[dict] = []
    checked = 0
    for country in FG1_WAVE_COUNTRIES:
        for scenario_code, scenario_row in scenarios.items():
            operation = scenario_row["operation"]
            checked += 1
            fixture = read_fg1_fixture_document(country, operation, scenario_code)
            missing_fixture_fields = [key for key in _FIXTURE_REQUIRED_FIELDS if key not in fixture]
            if missing_fixture_fields:
                errors.append(
                    {
                        "country_code": country,
                        "operation": operation,
                        "scenario": scenario_code,
                        "type": "fixture_missing_fields",
                        "fields": missing_fixture_fields,
                    }
                )
            if str(fixture.get("country_code", "")).upper() != country:
                errors.append(
                    {
                        "country_code": country,
                        "operation": operation,
                        "scenario": scenario_code,
                        "type": "fixture_country_mismatch",
                    }
                )
            if str(fixture.get("operation", "")).lower() != operation:
                errors.append(
                    {
                        "country_code": country,
                        "operation": operation,
                        "scenario": scenario_code,
                        "type": "fixture_operation_mismatch",
                    }
                )
            if str(fixture.get("scenario", "")).upper() != scenario_code:
                errors.append(
                    {
                        "country_code": country,
                        "operation": operation,
                        "scenario": scenario_code,
                        "type": "fixture_scenario_mismatch",
                    }
                )
            sim = simulate_fg1_stub(country=country, operation=operation, scenario=scenario_code)
            telemetry = sim.get("telemetry") or {}
            gov_raw = (sim.get("government_response") or {}).get("raw") or {}
            telemetry_required = ("trace_id", "provider_adapter", "fixture_source", "event_name", "timestamp")
            missing_telemetry = [key for key in telemetry_required if key not in telemetry]
            if missing_telemetry:
                errors.append(
                    {
                        "country_code": country,
                        "operation": operation,
                        "scenario": scenario_code,
                        "type": "simulate_missing_telemetry",
                        "fields": missing_telemetry,
                    }
                )
            raw_required = ("provider_adapter", "scenario", "operation", "authority_status", "country_code", "region", "trace_id")
            missing_raw = [key for key in raw_required if key not in gov_raw]
            if missing_raw:
                errors.append(
                    {
                        "country_code": country,
                        "operation": operation,
                        "scenario": scenario_code,
                        "type": "simulate_missing_government_raw",
                        "fields": missing_raw,
                    }
                )
    return {
        "wave": "FG-1-WAVE-1",
        "check_version": "fg1-envelope-check-v1",
        "checked_pairs": checked,
        "error_count": len(errors),
        "status": "OK" if len(errors) == 0 else "FAIL",
        "errors": errors,
    }

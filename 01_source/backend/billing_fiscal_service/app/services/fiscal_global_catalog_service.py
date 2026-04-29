from __future__ import annotations


def build_fiscal_global_catalog() -> dict:
    items = [
        {
            "country_code": "BR",
            "country_name": "Brazil",
            "region": "LATAM",
            "authority": "SEFAZ/SVRS",
            "document_types": ["NFE", "NFCE", "CTE", "MDFE"],
            "protocol": "SOAP/HTTPS",
            "stub_endpoint": "/stub/sefaz/nfe",
            "timezone": "America/Sao_Paulo",
            "currency": "BRL",
            "fiscal_mode_supported": ["stub", "real", "hybrid"],
            "priority_tier": "critical",
        },
        {
            "country_code": "PT",
            "country_name": "Portugal",
            "region": "EU",
            "authority": "AT",
            "document_types": ["SAFT", "ATCUD_INVOICE"],
            "protocol": "REST/HTTPS",
            "stub_endpoint": "/stub/atpt/faturas",
            "timezone": "Europe/Lisbon",
            "currency": "EUR",
            "fiscal_mode_supported": ["stub", "real", "hybrid"],
            "priority_tier": "critical",
        },
        {
            "country_code": "US",
            "country_name": "United States",
            "region": "NA",
            "authority": "IRS/State Authorities",
            "document_types": ["1099", "W2", "SALES_TAX_RETURN"],
            "protocol": "MeF XML/REST",
            "stub_endpoint": "/stub/irs/mef",
            "timezone": "America/New_York",
            "currency": "USD",
            "fiscal_mode_supported": ["stub", "real", "hybrid"],
            "priority_tier": "high",
        },
        {
            "country_code": "AU",
            "country_name": "Australia",
            "region": "APAC",
            "authority": "ATO",
            "document_types": ["BAS", "GST", "E_INVOICING"],
            "protocol": "REST/Peppol",
            "stub_endpoint": "/stub/au/ato",
            "timezone": "Australia/Sydney",
            "currency": "AUD",
            "fiscal_mode_supported": ["stub", "real", "hybrid"],
            "priority_tier": "high",
        },
        {
            "country_code": "PL",
            "country_name": "Poland",
            "region": "EU",
            "authority": "KAS/KSeF",
            "document_types": ["KSEF_E_INVOICE", "JPK_VAT"],
            "protocol": "REST/SOAP",
            "stub_endpoint": "/stub/pl/kas/jpk",
            "timezone": "Europe/Warsaw",
            "currency": "PLN",
            "fiscal_mode_supported": ["stub", "real", "hybrid"],
            "priority_tier": "high",
        },
        {
            "country_code": "CA",
            "country_name": "Canada",
            "region": "NA",
            "authority": "CRA/Revenu Quebec",
            "document_types": ["GST_HST", "T4", "QST"],
            "protocol": "REST/SOAP/XML",
            "stub_endpoint": "/stub/ca/cra",
            "timezone": "America/Toronto",
            "currency": "CAD",
            "fiscal_mode_supported": ["stub", "real", "hybrid"],
            "priority_tier": "high",
        },
        {
            "country_code": "FR",
            "country_name": "France",
            "region": "EU",
            "authority": "DGFIP/Chorus Pro",
            "document_types": ["FACTUR_X", "CHORUS_INVOICE"],
            "protocol": "REST/HTTPS",
            "stub_endpoint": "/stub/fr/chorus",
            "timezone": "Europe/Paris",
            "currency": "EUR",
            "fiscal_mode_supported": ["stub", "real", "hybrid"],
            "priority_tier": "medium",
        },
    ]
    return {
        "catalog_version": "fg0-v1",
        "items": items,
        "count": len(items),
    }


def build_fiscal_global_scenario_matrix() -> dict:
    operations = [
        "authorize",
        "cancel",
        "correct",
        "status",
    ]
    required_scenarios = [
        {"scenario": "AUTHORIZE_SUCCESS", "operation": "authorize", "canonical_status": "SUCCESS"},
        {"scenario": "AUTHORIZE_REJECTED", "operation": "authorize", "canonical_status": "BUSINESS_REJECTED"},
        {"scenario": "AUTHORIZE_SCHEMA_ERROR", "operation": "authorize", "canonical_status": "VALIDATION_ERROR"},
        {"scenario": "AUTHORIZE_TIMEOUT", "operation": "authorize", "canonical_status": "TIMEOUT"},
        {"scenario": "CANCEL_SUCCESS", "operation": "cancel", "canonical_status": "SUCCESS"},
        {"scenario": "CANCEL_DEADLINE_EXPIRED", "operation": "cancel", "canonical_status": "BUSINESS_REJECTED"},
        {"scenario": "CORRECT_SUCCESS", "operation": "correct", "canonical_status": "SUCCESS"},
        {"scenario": "STATUS_AUTHORIZED", "operation": "status", "canonical_status": "AUTHORIZED"},
        {"scenario": "STATUS_NOT_FOUND", "operation": "status", "canonical_status": "NOT_FOUND"},
    ]
    return {
        "matrix_version": "fg0-v1",
        "operations": operations,
        "required_scenarios": required_scenarios,
        "count": len(required_scenarios),
    }


def build_fiscal_fg1_wave_scope() -> dict:
    catalog = build_fiscal_global_catalog()
    matrix = build_fiscal_global_scenario_matrix()
    wave1_countries = ["US", "AU", "PL", "CA", "FR"]
    countries = [item for item in catalog["items"] if item.get("country_code") in wave1_countries]
    return {
        "scope_version": "fg1-wave1-v1",
        "wave": "FG-1-WAVE-1",
        "countries": countries,
        "required_scenarios": matrix["required_scenarios"],
        "country_count": len(countries),
        "scenario_count": len(matrix["required_scenarios"]),
    }

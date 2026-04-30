"""Escopo FG-1 Wave 1: ordem dos países, adapters stub e regiões permitidas.

Fonte única consumida por `fiscal_fg1_stub_service` e `fiscal_global_catalog_service`
para evitar divergência entre lista de onda e matriz de fixtures."""

from __future__ import annotations

# Ordem estável: usada em inventário, matriz de cobertura e escopo da API global.
FG1_WAVE_COUNTRIES: tuple[str, ...] = ("US", "AU", "PL", "CA", "FR", "PH", "ID", "NO")

FG1_ADAPTER_BY_COUNTRY: dict[str, str] = {
    "US": "irs_mef_stub_adapter_v1",
    "AU": "ato_stub_adapter_v1",
    "PL": "ksef_stub_adapter_v1",
    "CA": "cra_stub_adapter_v1",
    "FR": "chorus_stub_adapter_v1",
    "PH": "bir_stub_adapter_v1",
    "ID": "djp_stub_adapter_v1",
    "NO": "skatteetaten_stub_adapter_v1",
}

FG1_AUTHORITY_BY_COUNTRY: dict[str, str] = {
    "US": "IRS",
    "AU": "ATO",
    "PL": "KSeF",
    "CA": "CRA",
    "FR": "DGFiP",
    "PH": "BIR",
    "ID": "DJP",
    "NO": "Skatteetaten",
}

FG1_REGION_BY_COUNTRY: dict[str, str] = {
    "US": "NA",
    "AU": "OCEANIA",
    "PL": "EU",
    "CA": "NA",
    "FR": "EU",
    "PH": "APAC",
    "ID": "APAC",
    "NO": "EU",
}

FG1_ALLOWED_REGIONS_BY_COUNTRY: dict[str, tuple[str, ...]] = {
    "US": ("NA", "US-CA", "US-TX", "US-NY"),
    "AU": ("OCEANIA",),
    "PL": ("EU",),
    "CA": ("NA", "CA-QC"),
    "FR": ("EU",),
    "PH": ("APAC",),
    "ID": ("APAC",),
    "NO": ("EU",),
}

# F-2 — Motor de tributos BR (ICMS UF, PIS/COFINS) e PT (IVA por categoria CIVA).

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.invoice_model import Invoice
from app.models.product_fiscal_config import ProductFiscalConfig

logger = logging.getLogger(__name__)

# Alíquotas ICMS interestadual / interna aproximadas por UF (base legal CONFAZ — valores didáticos).
ICMS_UF_RATE: dict[str, float] = {
    "AC": 0.19,
    "AL": 0.19,
    "AM": 0.20,
    "AP": 0.18,
    "BA": 0.205,
    "CE": 0.20,
    "DF": 0.20,
    "ES": 0.17,
    "GO": 0.19,
    "MA": 0.23,
    "MG": 0.18,
    "MS": 0.17,
    "MT": 0.17,
    "PA": 0.19,
    "PB": 0.20,
    "PE": 0.20,
    "PI": 0.21,
    "PR": 0.20,
    "RJ": 0.20,
    "RN": 0.20,
    "RO": 0.195,
    "RR": 0.20,
    "RS": 0.20,
    "SC": 0.17,
    "SE": 0.20,
    "SP": 0.18,
    "TO": 0.20,
    "BR": 0.18,
}

PIS_RATE = 0.0065
COFINS_RATE = 0.03

IVA_PT_RATE: dict[str, float] = {
    "NORMAL": 0.23,
    "REDUZIDA": 0.13,
    "MINIMA": 0.06,
    "ISENTA": 0.0,
}


def _norm_region(region: str | None) -> str:
    return str(region or "").strip().upper()


def _tenant_fiscal(invoice: Invoice) -> dict[str, Any]:
    snap = invoice.order_snapshot or {}
    if isinstance(snap, dict):
        tf = snap.get("tenant_fiscal")
        if isinstance(tf, dict):
            return tf
    return {}


def _is_simples_nacional(invoice: Invoice) -> bool:
    r = str(_tenant_fiscal(invoice).get("regime", "")).upper()
    return "SIMPLES" in r


def _icms_cst_for_line(simples: bool) -> str:
    return "102" if simples else "000"


def _resolve_icms_rate_br(invoice: Invoice, simples: bool) -> float:
    if simples:
        return 0.0
    reg = _norm_region(invoice.region)
    return ICMS_UF_RATE.get(reg, ICMS_UF_RATE["SP"])


def _load_product_config(db: Session | None, sku_id: str) -> ProductFiscalConfig | None:
    if db is None or not sku_id:
        return None
    return (
        db.query(ProductFiscalConfig)
        .filter(ProductFiscalConfig.sku_id == sku_id)
        .filter(ProductFiscalConfig.is_active.is_(True))
        .first()
    )


def _invoice_lines(invoice: Invoice) -> list[dict[str, Any]]:
    raw = (invoice.items_json or {}).get("lines") if isinstance(invoice.items_json, dict) else None
    lines: list[dict[str, Any]] = []
    if isinstance(raw, list) and raw:
        for i, row in enumerate(raw):
            if not isinstance(row, dict):
                continue
            qty = int(row.get("quantity") or 1)
            tac = row.get("total_amount_cents")
            uac = row.get("unit_amount_cents")
            try:
                total = int(tac) if tac is not None else int(uac or 0) * max(qty, 1)
            except (TypeError, ValueError):
                total = 0
            ncm = row.get("ncm")
            if ncm is not None:
                ncm = str(ncm).strip() or None
            line: dict[str, Any] = {
                "line_index": i,
                "sku_id": str(row.get("sku_id") or ""),
                "quantity": qty,
                "total_amount_cents": total,
                "metadata": row.get("metadata") or row.get("metadata_json") or {},
            }
            if ncm:
                line["ncm"] = ncm
            lines.append(line)
        return lines

    order = (invoice.order_snapshot or {}).get("order") or {}
    sku = str(order.get("sku_id") or "")
    amt = int(invoice.amount_cents or 0)
    if amt <= 0:
        return []
    return [
        {
            "line_index": 0,
            "sku_id": sku,
            "quantity": 1,
            "total_amount_cents": amt,
            "metadata": {},
        }
    ]


def _round_cents(value: float) -> int:
    return int(round(value))


def build_tax_breakdown(db: Session | None, invoice: Invoice) -> dict[str, Any]:
    """
    Monta tax_breakdown_json por linha. Valida soma das bases vs amount_cents (±1 centavo).
    """
    country = str(invoice.country or "").strip().upper()
    lines_in = _invoice_lines(invoice)
    if not lines_in:
        return {
            "country": country,
            "lines": [],
            "summary": {
                "total_taxable_cents": 0,
                "total_tax_cents": 0,
                "invoice_amount_cents": int(invoice.amount_cents or 0),
            },
            "warnings": ["no_lines"],
        }

    out_lines: list[dict[str, Any]] = []
    total_taxable = 0
    total_tax = 0

    if country not in ("BR", "PT"):
        base = sum(int(x["total_amount_cents"]) for x in lines_in)
        return {
            "country": country,
            "lines": [
                {
                    "line_index": row["line_index"],
                    "sku_id": row["sku_id"],
                    "taxable_base_cents": int(row["total_amount_cents"]),
                    "note": "Motor F-2: país sem regra dedicada (imposto zero).",
                }
                for row in lines_in
            ],
            "summary": {
                "total_taxable_cents": base,
                "total_tax_cents": 0,
                "invoice_amount_cents": int(invoice.amount_cents or 0),
            },
            "warnings": ["unsupported_country_tax_rules"],
        }

    if country == "PT":
        for row in lines_in:
            sku = row["sku_id"]
            cfg = _load_product_config(db, sku)
            cat = str((cfg and cfg.iva_category) or "NORMAL").upper()
            rate = IVA_PT_RATE.get(cat, IVA_PT_RATE["NORMAL"])
            base = int(row["total_amount_cents"])
            iva = _round_cents(base * rate)
            total_taxable += base
            total_tax += iva
            out_lines.append(
                {
                    "line_index": row["line_index"],
                    "sku_id": sku,
                    "ncm_code": cfg.ncm_code if cfg else None,
                    "iva_category": cat,
                    "iva_rate": rate,
                    "taxable_base_cents": base,
                    "iva_cents": iva,
                }
            )
    else:
        simples = _is_simples_nacional(invoice)
        icms_rate = _resolve_icms_rate_br(invoice, simples)
        cst = _icms_cst_for_line(simples)
        for row in lines_in:
            sku = row["sku_id"]
            cfg = _load_product_config(db, sku)
            ncm = cfg.ncm_code if cfg else None
            base = int(row["total_amount_cents"])
            icms = _round_cents(base * icms_rate) if icms_rate > 0 else 0
            pis = _round_cents(base * PIS_RATE)
            cofins = _round_cents(base * COFINS_RATE)
            line_tax = icms + pis + cofins
            total_taxable += base
            total_tax += line_tax
            out_lines.append(
                {
                    "line_index": row["line_index"],
                    "sku_id": sku,
                    "ncm_code": ncm,
                    "icms_cst": (cfg.icms_cst if cfg else None) or cst,
                    "pis_cst": (cfg.pis_cst if cfg else None) or ("49" if simples else "01"),
                    "cofins_cst": (cfg.cofins_cst if cfg else None) or ("49" if simples else "01"),
                    "icms_rate": icms_rate,
                    "taxable_base_cents": base,
                    "icms_cents": icms,
                    "pis_cents": pis,
                    "cofins_cents": cofins,
                    "regime_simples": simples,
                }
            )

    inv_amt = int(invoice.amount_cents or 0)
    if inv_amt and abs(total_taxable - inv_amt) > 1:
        logger.warning(
            "tax_breakdown_amount_mismatch order_id=%s taxable=%s invoice=%s",
            invoice.order_id,
            total_taxable,
            inv_amt,
        )

    return {
        "country": country,
        "region": invoice.region,
        "regime_simples_nacional": _is_simples_nacional(invoice) if country == "BR" else False,
        "lines": out_lines,
        "summary": {
            "total_taxable_cents": total_taxable,
            "total_tax_cents": total_tax,
            "invoice_amount_cents": inv_amt,
        },
    }


def apply_tax_to_invoice(db: Session | None, invoice: Invoice) -> None:
    """Persiste breakdown no ORM (caller faz commit/flush)."""
    invoice.tax_breakdown_json = build_tax_breakdown(db, invoice)
    tb = invoice.tax_breakdown_json or {}
    summary = tb.get("summary") or {}
    invoice.tax_details = {
        "engine": "tax_service",
        "version": 2,
        "country": tb.get("country"),
        "summary": summary,
        "line_count": len(tb.get("lines") or []),
    }

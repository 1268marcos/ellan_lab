# I-2 — Política de cancelamento NFC-e (BR) e fallback para outros países (stub).

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


class CancelPolicyAction(str, enum.Enum):
    """Ação fiscal recomendada após emissão (referência SEFAZ NFC-e modelo 65)."""

    VOID_NFCE = "VOID_NFCE"
    CORRECTION_LETTER_REQUIRED = "CORRECTION_LETTER_REQUIRED"
    COMPLEMENTARY_INVOICE_REQUIRED = "COMPLEMENTARY_INVOICE_REQUIRED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass(frozen=True)
class CancelPolicyResult:
    action: CancelPolicyAction
    detail: dict[str, Any]


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def resolve_cancel_policy(
    *,
    issued_at: datetime,
    now: datetime,
    country: str,
    fiscal_doc_subtype: str | None = None,
) -> CancelPolicyResult:
    """
    BR / NFC-e 65 (referência operacional):
      - < 30 min: evento de cancelamento (void)
      - 30 min – 24 h: carta de correção (CC-e)
      - > 24 h: nota complementar / análise manual conforme caso
    Outros países: MANUAL_REVIEW até integração específica (I-2/F-3).
    """
    c = (country or "").strip().upper()
    subtype = (fiscal_doc_subtype or "").strip().upper() or "NFC_E_65"

    issued = _ensure_utc(issued_at)
    ref = _ensure_utc(now)
    delta: timedelta = ref - issued
    sec = max(0.0, delta.total_seconds())

    detail: dict[str, Any] = {
        "country": c,
        "fiscal_doc_subtype": subtype,
        "seconds_since_issue": int(sec),
    }

    if c != "BR":
        return CancelPolicyResult(CancelPolicyAction.MANUAL_REVIEW, {**detail, "reason": "non_br_country"})

    if sec < 30 * 60:
        return CancelPolicyResult(CancelPolicyAction.VOID_NFCE, {**detail, "window": "lt_30m"})
    if sec < 24 * 3600:
        return CancelPolicyResult(
            CancelPolicyAction.CORRECTION_LETTER_REQUIRED,
            {**detail, "window": "30m_to_24h"},
        )
    return CancelPolicyResult(
        CancelPolicyAction.COMPLEMENTARY_INVOICE_REQUIRED,
        {**detail, "window": "gt_24h"},
    )

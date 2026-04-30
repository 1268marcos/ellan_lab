"""F3C-STUB-01 — assinatura A1 em modo *dry-run* (sem certificado A1 real).

Gera metadados criptográficos **verificáveis localmente** usando HMAC-SHA256 sobre o
digest SHA-256 do `xml_preview` NFC-e (stub). Isto não é assinatura XMLDSig nem
substitui envio à SEFAZ; serve apenas para exercitar o pipeline e flags
`FISCAL_A1_DRY_RUN_*` até existir integração A1 real.

Verificação: `verify_a1_dry_run_signature` (usada pelo endpoint admin `/verify`).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from typing import Any

from app.core.config import settings


def _secret_bytes() -> bytes:
    raw = (settings.fiscal_a1_dry_run_hmac_secret or "").strip()
    if raw:
        return raw.encode("utf-8")
    # Valor por omissão apenas para dev/lab; definir FISCAL_A1_DRY_RUN_HMAC_SECRET em ambientes partilhados.
    return b"FISCAL_A1_DRY_RUN_DEV_ONLY"


def compute_content_digest_sha256(xml_preview: str) -> str:
    body = (xml_preview or "").encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def build_dry_run_hmac_signature_b64(*, xml_preview: str) -> str:
    """Assinatura sintética: HMAC-SHA256(secret, sha256_hex_utf8)."""
    digest_hex = compute_content_digest_sha256(xml_preview)
    sig = hmac.new(_secret_bytes(), digest_hex.encode("ascii"), hashlib.sha256).digest()
    return base64.b64encode(sig).decode("ascii")


def build_a1_dry_run_signature_extensions(*, xml_preview: str, access_key: str) -> dict[str, Any]:
    digest_hex = compute_content_digest_sha256(xml_preview)
    sig_b64 = build_dry_run_hmac_signature_b64(xml_preview=xml_preview)
    return {
        "dry_run_content_sha256_hex": digest_hex,
        "dry_run_signature_b64": sig_b64,
        "dry_run_signature_algorithm": "HMAC-SHA256(secret, SHA256(xml_preview)_hex)",
        "dry_run_nonce": secrets.token_hex(8),
        "dry_run_access_key_hint": str(access_key or "")[:32],
    }


def verify_a1_dry_run_signature(*, xml_preview: str, signature_block: dict[str, Any] | None) -> bool:
    if not signature_block or not isinstance(signature_block, dict):
        return False
    expected_b64 = build_dry_run_hmac_signature_b64(xml_preview=xml_preview)
    got = str(signature_block.get("dry_run_signature_b64") or "").strip()
    if not got:
        return False
    try:
        a = base64.b64decode(expected_b64)
        b = base64.b64decode(got)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(a, b)


def build_a1_dry_run_status_payload() -> dict[str, Any]:
    return {
        "fiscal_a1_dry_run_enabled": bool(settings.fiscal_a1_dry_run_enabled),
        "fiscal_a1_dry_run_cert_ref": settings.fiscal_a1_dry_run_cert_ref,
        "fiscal_a1_dry_run_hmac_secret_configured": bool(
            str(settings.fiscal_a1_dry_run_hmac_secret or "").strip()
        ),
        "algorithm": "HMAC-SHA256(secret, SHA256(xml_preview)_hex)",
        "note": "Dry-run não usa certificado A1; não enviar este XML como documento oficial.",
    }

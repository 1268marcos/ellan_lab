from __future__ import annotations

from app.models.invoice_model import Invoice

def validate_stub_contract_compliance(*, country: str, operation: str, stub_response: dict) -> dict:
    """
    Valida se a resposta do stub está aderente ao contrato esperado do provider real (por país/operação).

    Parâmetros:
        country (str): código do país (ex: "BR", "PT")
        operation (str): operação fiscal ("issue", "cancel", "correction")
        stub_response (dict): resposta do stub a ser validada

    Retorna:
        dict: {
            "compliant": bool,
            "missing_fields": [str, ...],
            "type_mismatches": [str, ...],
            "warnings": [str, ...],
            "country": country,
            "operation": operation
        }
    """
    import datetime

    # 1. Mapas de campos obrigatórios por país/operação
    # (pode ser expandido para mais países/operações conforme necessidade)
    REQUIRED_FIELDS = {
        "BR": {
            "issue": [
                ("status", str),
                ("invoice_number", str),
                ("invoice_series", str),
                ("access_key", str),
                ("government_response", dict),
            ],
            "cancel": [
                ("status", str),
                ("access_key", str),
                ("government_response", dict)
            ],
            "correction": [
                ("status", str),
                ("access_key", str),
                ("correction_text", str),
                ("government_response", dict)
            ]
        },
        "PT": {
            "issue": [
                ("status", str),
                ("invoice_number", str),
                ("invoice_series", str),
                ("access_key", str),
                ("government_response", dict),
            ],
            "cancel": [
                ("status", str),
                ("access_key", str),
                ("government_response", dict),
            ],
            "correction": [
                ("status", str),
                ("access_key", str),
                ("correction_text", str),
                ("government_response", dict),
            ]
        },
    }
    OPTIONAL_FIELDS = [
        ("receipt_number", str),
        ("protocol_number", str),
        ("xml_content", dict),  # pode variar (dict ou str); warning se não for dict/str
    ]
    # Campos obrigatórios dentro de government_response
    GOVERNMENT_RESPONSE_REQUIRED = [
        ("provider_namespace", str),
        ("provider_status", str),
        ("provider_code", str),
    ]

    # Função auxiliar para validar ISO timestamps
    def is_iso8601(s):
        try:
            if not isinstance(s, str):
                return False
            # datetime.fromisoformat aceita alguns formatos inválidos, então checagem adicional:
            # ISO com 'Z' no final não é aceito por fromisoformat, então tratamos especificamente
            if s.endswith('Z'):
                s = s[:-1] + '+00:00'
            datetime.datetime.fromisoformat(s)
            return True
        except Exception:
            return False

    country = (country or "").upper()
    operation = (operation or "").lower()
    fields_required = REQUIRED_FIELDS.get(country, {}).get(operation, [])

    missing_fields = []
    type_mismatches = []
    warnings = []

    # 2. Verificar campos obrigatórios
    for fname, ftype in fields_required:
        if fname not in stub_response:
            missing_fields.append(fname)
        else:
            value = stub_response[fname]
            # Permite str/int para campos numéricos, mas força str para campos textuais
            if ftype == str and not isinstance(value, str):
                type_mismatches.append(f"{fname} (expected str, got {type(value).__name__})")
            if ftype == dict and not isinstance(value, dict):
                type_mismatches.append(f"{fname} (expected dict, got {type(value).__name__})")

    # 3. government_response estrutura interna
    if "government_response" in stub_response and isinstance(stub_response.get("government_response"), dict):
        gr = stub_response["government_response"]
        for gr_field, gr_type in GOVERNMENT_RESPONSE_REQUIRED:
            if gr_field not in gr:
                missing_fields.append(f"government_response.{gr_field}")
            else:
                if gr_type == str and not isinstance(gr[gr_field], str):
                    type_mismatches.append(f"government_response.{gr_field} (expected str, got {type(gr[gr_field]).__name__})")
    else:
        if any(f[0] == "government_response" for f in fields_required):
            missing_fields.append("government_response")

    # 4. Tipos de dados especiais: timestamps ISO (exemplo: processed_at, issued_at)
    # Não são obrigatórios, mas avisamos se estão presentes em formato errado.
    for ts_field in ["processed_at", "issued_at", "cancelled_at"]:
        if ts_field in stub_response and stub_response[ts_field] is not None:
            if not is_iso8601(stub_response[ts_field]):
                warnings.append(f"{ts_field} is not a valid ISO 8601 timestamp")

    # 5. Verificar campos opcionais documentados
    for opt_field, opt_type in OPTIONAL_FIELDS:
        if opt_field in stub_response:
            value = stub_response[opt_field]
            if opt_type == str and value is not None and not isinstance(value, str):
                warnings.append(f"{opt_field} is not string (optional, got {type(value).__name__})")
            if opt_field == "xml_content" and value is not None and not (isinstance(value, dict) or isinstance(value, str)):
                warnings.append(f"xml_content is not dict or str (got {type(value).__name__})")

    compliant = not missing_fields and not type_mismatches

    return {
        "compliant": compliant,
        "missing_fields": missing_fields,
        "type_mismatches": type_mismatches,
        "warnings": warnings,
        "country": country,
        "operation": operation,
    }

# ===
# Lista de campos obrigatórios por país/operação:
#
# BR / issue:
#   - status (str)
#   - invoice_number (str)
#   - invoice_series (str)
#   - access_key (str)
#   - government_response (dict: provider_namespace, provider_status, provider_code)
#
# BR / cancel:
#   - status (str)
#   - access_key (str)
#   - government_response (dict)
#
# BR / correction:
#   - status (str)
#   - access_key (str)
#   - correction_text (str)
#   - government_response (dict)
#
# PT é equivalente ao BR para as operações principais.
#
# government_response:
#   - provider_namespace (str)
#   - provider_status (str)
#   - provider_code (str)
#
# Campos opcionais sugeridos (para warning, não erro):
#   - receipt_number (str)
#   - protocol_number (str)
#   - xml_content (dict ou str)
#
#
# ===
# Integração: como usar no pipeline CI/CD para validar stubs antes do deploy
#
# 1. Em seus testes automatizados (pytest), chame validate_stub_contract_compliance para cada resposta dos stubs:
#
#    result = validate_stub_contract_compliance(country="BR", operation="issue", stub_response=resp)
#    assert result["compliant"], f"Contrato inválido: {result}"
#
# 2. Opcional: gerar um relatório agregando as falhas, exibindo missing_fields/type_mismatches para cada operação.
# 3. Você pode rodar isso como parte de um step CI que executa suas suites de smoke test dos endpoints stub, impedindo deploy se algum contrato essencial quebrar.

def build_issue_payload(*, invoice: Invoice, country: str) -> dict:
    payload_json = invoice.payload_json if isinstance(invoice.payload_json, dict) else {}
    return {
        "invoice_id": invoice.id,
        "order_id": invoice.order_id,
        "country": country,
        "region": invoice.region,
        "amount_cents": int(invoice.amount_cents or 0),
        "currency": invoice.currency,
        "payment_method": invoice.payment_method,
        "tax_breakdown_json": invoice.tax_breakdown_json,
        "order_snapshot": invoice.order_snapshot,
        # STUB controls for provider simulation (non-production fields)
        "stub_scenario": payload_json.get("stub_scenario"),
        "stub_success_on_attempt": payload_json.get("stub_success_on_attempt"),
        "stub_batch_poll_count": payload_json.get("stub_batch_poll_count"),
        "ready_after_polls": payload_json.get("ready_after_polls"),
        "idempotency_key": payload_json.get("idempotency_key"),
    }


def build_cancel_payload(*, invoice: Invoice, country: str) -> dict:
    return {
        "invoice_id": invoice.id,
        "order_id": invoice.order_id,
        "country": country,
        "access_key": invoice.access_key,
    }


def build_correction_payload(*, invoice: Invoice, country: str, correction_text: str | None) -> dict:
    return {
        "invoice_id": invoice.id,
        "order_id": invoice.order_id,
        "country": country,
        "access_key": invoice.access_key,
        "correction_text": correction_text,
    }


def normalize_issue_response(*, invoice: Invoice, country: str, provider: str, raw: dict) -> dict:
    if country == "BR":
        invoice_number = raw.get("invoice_number") or raw.get("number") or f"SVRS-{invoice.id[-6:]}"
        invoice_series = raw.get("invoice_series") or raw.get("series") or "SVRS-1"
        access_key = raw.get("access_key") or raw.get("chave") or invoice.access_key
        status = "AUTHORIZED"
        code = "100"
        message = "Autorizado."
        xml_default = {"format": "xml_real_provider"}
    else:
        invoice_number = raw.get("invoice_number") or raw.get("number") or f"AT-{invoice.id[-6:]}"
        invoice_series = raw.get("invoice_series") or raw.get("series") or "AT-1"
        access_key = raw.get("access_key") or raw.get("hash") or invoice.access_key
        status = "ACCEPTED"
        code = "AT-200"
        message = "Documento aceite."
        xml_default = {"format": "saft_real_provider"}

    gov = raw.get("government_response") if isinstance(raw.get("government_response"), dict) else {}
    if not gov:
        gov = {
            "provider_namespace": provider,
            "provider_status": str(raw.get("provider_status") or raw.get("status") or status),
            "provider_code": str(raw.get("provider_code") or raw.get("code") or code),
            "provider_message": str(raw.get("provider_message") or raw.get("message") or message),
            "receipt_number": raw.get("receipt_number"),
            "protocol_number": raw.get("protocol_number"),
            "raw": raw,
        }

    return {
        "provider": provider,
        "country": country,
        "status": "ISSUED",
        "invoice_number": invoice_number,
        "invoice_series": invoice_series,
        "access_key": access_key,
        "tax_details": raw.get("tax_details") or invoice.tax_details or {},
        "xml_content": raw.get("xml_content") or invoice.xml_content or xml_default,
        "government_response": gov,
    }


def normalize_cancel_response(*, invoice: Invoice, country: str, provider: str, raw: dict) -> dict:
    return {
        "provider": provider,
        "country": country,
        "cancel_status": str(raw.get("cancel_status") or raw.get("status") or "CANCELLED"),
        "access_key": raw.get("access_key") or invoice.access_key,
        "protocol_number": raw.get("protocol_number"),
        "processed_at": raw.get("processed_at"),
        "raw": raw,
    }


def normalize_correction_response(
    *,
    invoice: Invoice,
    country: str,
    provider: str,
    correction_text: str | None,
    raw: dict,
) -> dict:
    response = {
        "provider": provider,
        "kind": "cce" if country == "BR" else "correction",
        "country": country,
        "access_key": raw.get("access_key") or invoice.access_key,
        "correction_text": str(raw.get("correction_text") or correction_text or "")[:1000],
        "protocol_number": raw.get("protocol_number"),
        "processed_at": raw.get("processed_at"),
        "raw": raw,
    }
    if country == "BR":
        response["sequence"] = int(raw.get("sequence") or 1)
        response["xml_event_preview"] = raw.get("xml_event_preview")
    return response

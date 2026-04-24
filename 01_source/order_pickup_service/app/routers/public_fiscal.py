# 01_source/order_pickup_service/app/routers/public_fiscal.py
from __future__ import annotations

import json
from html import escape

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.fiscal_document import FiscalDocument
from app.integrations.billing_fiscal_client import fetch_invoice_by_receipt_code
from app.services.fiscal_read_adapter import fiscal_read_view_from_billing_invoice
from app.services.fiscal_resolve import FiscalReadable

from app.core.datetime_utils import to_iso_utc


router = APIRouter(prefix="/public/fiscal", tags=["public-fiscal"])


def _safe_payload_section(payload: dict, key: str) -> dict:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _coalesce(*values):
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _normalize_receipt_code(receipt_code: str) -> str:
    normalized_code = str(receipt_code or "").strip().upper()
    if not normalized_code:
        raise HTTPException(status_code=400, detail="receipt_code is required")
    return normalized_code


def _serialize_fiscal_document(doc: FiscalReadable) -> dict:
    payload = doc.payload_json or {}

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = {}

    status = payload.get("mode") or "SIMULATED"

    order_payload = _safe_payload_section(payload, "order")
    allocation_payload = _safe_payload_section(payload, "allocation")
    pickup_payload = _safe_payload_section(payload, "pickup")

    return {
        "ok": True,
        "receipt_code": doc.receipt_code,
        "document": {
            "id": doc.id,
            "order_id": doc.order_id,
            "document_type": doc.document_type,
            "status": status,
            "channel": doc.channel,
            "region": doc.region,
            "amount_cents": doc.amount_cents,
            "currency": doc.currency,
            "delivery_mode": doc.delivery_mode,
            "send_status": doc.send_status,
            "send_target": doc.send_target,
            "print_status": doc.print_status,
            "print_site_path": doc.print_site_path,
            "issued_at": doc.issued_at.isoformat() if doc.issued_at else None,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        },
        "order": {
            "id": _coalesce(order_payload.get("id"), doc.order_id),
            "channel": _coalesce(order_payload.get("channel"), doc.channel),
            "region": _coalesce(order_payload.get("region"), doc.region),
            "totem_id": order_payload.get("totem_id"),
            "sku_id": order_payload.get("sku_id"),
            "amount_cents": _coalesce(order_payload.get("amount_cents"), doc.amount_cents),
            "payment_method": order_payload.get("payment_method"),
            "gateway_transaction_id": order_payload.get("gateway_transaction_id"),
            "paid_at": order_payload.get("paid_at"),
            "pickup_deadline_at": order_payload.get("pickup_deadline_at"),
        },
        "allocation": {
            "id": allocation_payload.get("id"),
            "locker_id": allocation_payload.get("locker_id"),
            "slot": allocation_payload.get("slot"),
            "state": allocation_payload.get("state"),
        },
        "pickup": {
            "id": pickup_payload.get("id"),
            "locker_id": pickup_payload.get("locker_id"),
            "machine_id": pickup_payload.get("machine_id"),
            "slot": pickup_payload.get("slot"),
            "status": pickup_payload.get("status"),
            "lifecycle_stage": pickup_payload.get("lifecycle_stage"),
        },
        "payload": payload,
        "links": {
            "print_html": f"/public/fiscal/print/{doc.receipt_code}",
            "json": f"/public/fiscal/by-code/{doc.receipt_code}",
        },
    }


def _build_print_html(doc: FiscalReadable) -> str:
    data = _serialize_fiscal_document(doc)
    payload = data.get("payload") or {}
    order = data.get("order") or {}
    allocation = data.get("allocation") or {}
    pickup = data.get("pickup") or {}
    document = data.get("document") or {}

    receipt_code = escape(str(doc.receipt_code or ""))
    order_id = escape(str(doc.order_id or ""))
    document_type = escape(str(doc.document_type or ""))
    channel = escape(str(doc.channel or ""))
    region = escape(str(doc.region or ""))
    currency = escape(str(doc.currency or ""))
    amount_cents = int(doc.amount_cents or 0)
    amount_value = f"{amount_cents / 100:.2f}"
    delivery_mode = escape(str(doc.delivery_mode or ""))
    send_status = escape(str(doc.send_status or ""))
    send_target = escape(str(doc.send_target or ""))
    print_status = escape(str(doc.print_status or ""))
    issued_at = escape(doc.issued_at.isoformat() if doc.issued_at else "")
    purchase_reference = escape(str(payload.get("purchase_reference") or order_id))
    print_label = escape(str(payload.get("print_label") or "Comprovante fiscal simulado"))

    sku_id = escape(str(order.get("sku_id") or ""))
    totem_id = escape(str(order.get("totem_id") or ""))
    payment_method = escape(str(order.get("payment_method") or ""))
    gateway_transaction_id = escape(str(order.get("gateway_transaction_id") or ""))
    pickup_id = escape(str(pickup.get("id") or ""))
    pickup_slot = escape(str(pickup.get("slot") or allocation.get("slot") or ""))
    locker_id = escape(str(pickup.get("locker_id") or allocation.get("locker_id") or ""))
    machine_id = escape(str(pickup.get("machine_id") or ""))
    allocation_id = escape(str(allocation.get("id") or ""))

    json_preview = escape(
        json.dumps(data, ensure_ascii=False, indent=2)
    )

    title = f"Comprovante {receipt_code}"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>{title}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root {{
      --border: #d9d9d9;
      --text: #1f1f1f;
      --muted: #666;
      --bg: #fffff5;
      --soft: #f6f6f6;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      padding: 24px;
      background: var(--soft);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
    }}
    .page {{
      max-width: 900px;
      margin: 0 auto;
    }}
    .actions {{
      display: flex;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }}
    .btn {{
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      padding: 10px 14px;
      border-radius: 10px;
      cursor: pointer;
      font-size: 14px;
      text-decoration: none;
      display: inline-block;
    }}
    .card {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }}
    h1 {{
      margin: 0 0 8px 0;
      font-size: 24px;
    }}
    .subtitle {{
      margin: 0 0 20px 0;
      color: var(--muted);
      font-size: 14px;
    }}
    .code {{
      display: inline-block;
      font-weight: 700;
      letter-spacing: 0.08em;
      border: 1px dashed var(--border);
      padding: 10px 12px;
      border-radius: 10px;
      background: #fafafa;
      margin: 8px 0 20px 0;
    }}
    .section {{
      margin-top: 20px;
    }}
    .section h2 {{
      margin: 0 0 10px 0;
      font-size: 16px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    td {{
      padding: 10px 8px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
      font-size: 14px;
    }}
    td:first-child {{
      width: 240px;
      color: var(--muted);
    }}
    pre {{
      margin: 0;
      padding: 14px;
      background: #fafafa;
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: auto;
      font-size: 12px;
      line-height: 1.45;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    .footer {{
      margin-top: 24px;
      font-size: 12px;
      color: var(--muted);
      line-height: 1.5;
    }}
    @media print {{
      body {{
        background: #fffff5;
        padding: 0;
      }}
      .page {{
        max-width: none;
      }}
      .actions {{
        display: none;
      }}
      .card {{
        border: none;
        box-shadow: none;
        border-radius: 0;
        padding: 0;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <div class="actions">
      <button class="btn" onclick="window.print()">Imprimir</button>
      <button class="btn" onclick="window.print()">Baixar PDF</button>
      <a class="btn" href="/public/fiscal/by-code/{receipt_code}" target="_blank" rel="noopener noreferrer">Ver JSON</a>
      <button class="btn" onclick="window.close()">Fechar</button>
    </div>

    <div class="card">
      <h1>Comprovante fiscal simulado</h1>
      <p class="subtitle">{print_label}</p>

      <div class="code">{receipt_code}</div>

      <div class="section">
        <h2>Dados do documento</h2>
        <table>
          <tr><td>Código do comprovante</td><td>{receipt_code}</td></tr>
          <tr><td>Pedido</td><td>{order_id}</td></tr>
          <tr><td>Referência da compra</td><td>{purchase_reference}</td></tr>
          <tr><td>Tipo de documento</td><td>{document_type}</td></tr>
          <tr><td>Canal</td><td>{channel}</td></tr>
          <tr><td>Região</td><td>{region}</td></tr>
          <tr><td>Emitido em</td><td>{issued_at}</td></tr>
        </table>
      </div>

      <div class="section">
        <h2>Dados financeiros</h2>
        <table>
          <tr><td>Valor</td><td>{currency} {amount_value}</td></tr>
          <tr><td>Moeda</td><td>{currency}</td></tr>
          <tr><td>Método de pagamento</td><td>{payment_method}</td></tr>
          <tr><td>Gateway transaction id</td><td>{gateway_transaction_id}</td></tr>
        </table>
      </div>

      <div class="section">
        <h2>Dados operacionais</h2>
        <table>
          <tr><td>SKU</td><td>{sku_id}</td></tr>
          <tr><td>Totem</td><td>{totem_id}</td></tr>
          <tr><td>Allocation ID</td><td>{allocation_id}</td></tr>
          <tr><td>Pickup ID</td><td>{pickup_id}</td></tr>
          <tr><td>Locker ID</td><td>{locker_id}</td></tr>
          <tr><td>Machine ID</td><td>{machine_id}</td></tr>
          <tr><td>Slot</td><td>{pickup_slot}</td></tr>
        </table>
      </div>

      <div class="section">
        <h2>Entrega do comprovante</h2>
        <table>
          <tr><td>Modo</td><td>{delivery_mode}</td></tr>
          <tr><td>Status de envio</td><td>{send_status}</td></tr>
          <tr><td>Destino</td><td>{send_target}</td></tr>
          <tr><td>Status de impressão</td><td>{print_status}</td></tr>
        </table>
      </div>

      <div class="section">
        <h2>Pré-visualização JSON</h2>
        <pre>{json_preview}</pre>
      </div>

      <div class="footer">
        Este documento é uma representação simulada persistida localmente para auditoria e impressão.
        A emissão fiscal oficial continua sendo responsabilidade do fluxo fiscal oficial do sistema.
      </div>
    </div>
  </div>
</body>
</html>
"""




def _build_search_html() -> str:
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>Buscar comprovante fiscal</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root {
      --border: #d9d9d9;
      --text: #1f1f1f;
      --muted: #666;
      --bg: #fffff5;
      --soft: #f6f6f6;
      --accent: #111827;
    }
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      padding: 24px;
      background: var(--soft);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
    }
    .page {
      max-width: 900px;
      margin: 0 auto;
    }
    .card {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    h1 {
      margin: 0 0 8px 0;
      font-size: 24px;
    }
    .subtitle {
      margin: 0 0 20px 0;
      color: var(--muted);
      font-size: 14px;
    }
    .search-row {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
      margin-bottom: 18px;
    }
    input[type="text"] {
      width: 100%;
      padding: 12px 14px;
      border-radius: 10px;
      border: 1px solid var(--border);
      font-size: 14px;
      text-transform: uppercase;
    }
    .btn {
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      padding: 12px 14px;
      border-radius: 10px;
      cursor: pointer;
      font-size: 14px;
      text-decoration: none;
      display: inline-block;
    }
    .btn-primary {
      background: var(--accent);
      color: white;
      border-color: var(--accent);
    }
    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 14px;
    }
    .hidden {
      display: none;
    }
    .result {
      margin-top: 20px;
      padding-top: 18px;
      border-top: 1px solid var(--border);
    }
    .code {
      display: inline-block;
      font-weight: 700;
      letter-spacing: 0.08em;
      border: 1px dashed var(--border);
      padding: 10px 12px;
      border-radius: 10px;
      background: #fafafa;
      margin: 8px 0 16px 0;
    }
    table {
      width: 100%;
      border-collapse: collapse;
    }
    td {
      padding: 10px 8px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
      font-size: 14px;
    }
    td:first-child {
      width: 230px;
      color: var(--muted);
    }
    .error {
      margin-top: 16px;
      padding: 12px 14px;
      border: 1px solid #f0caca;
      background: #fff6f6;
      color: #8a1c1c;
      border-radius: 10px;
      font-size: 14px;
    }
    .muted {
      color: var(--muted);
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="card">
      <h1>Buscar comprovante fiscal</h1>
      <p class="subtitle">Digite o código do comprovante, como KSK-57FC92582464 ou ONL-E4D88D3F9C48.</p>

      <div class="search-row">
        <input
          id="receiptCode"
          type="text"
          placeholder="Ex.: KSK-57FC92582464"
          autocomplete="off"
        />
        <button id="searchBtn" class="btn btn-primary">Buscar</button>
      </div>

      <div id="errorBox" class="error hidden"></div>

      <div id="resultBox" class="result hidden">
        <div id="receiptCodeBox" class="code"></div>

        <table>
          <tr><td>Pedido</td><td id="orderId"></td></tr>
          <tr><td>Tipo de documento</td><td id="documentType"></td></tr>
          <tr><td>Canal</td><td id="channel"></td></tr>
          <tr><td>Região</td><td id="region"></td></tr>
          <tr><td>Valor</td><td id="amount"></td></tr>
          <tr><td>Método de pagamento</td><td id="paymentMethod"></td></tr>
          <tr><td>Gateway transaction id</td><td id="gatewayTransactionId"></td></tr>
          <tr><td>SKU</td><td id="skuId"></td></tr>
          <tr><td>Totem</td><td id="totemId"></td></tr>
          <tr><td>Allocation ID</td><td id="allocationId"></td></tr>
          <tr><td>Pickup ID</td><td id="pickupId"></td></tr>
          <tr><td>Locker ID</td><td id="lockerId"></td></tr>
          <tr><td>Machine ID</td><td id="machineId"></td></tr>
          <tr><td>Slot</td><td id="slot"></td></tr>
        </table>

        <div class="actions">
          <a id="openPrintBtn" class="btn" href="#" target="_blank" rel="noopener noreferrer">Abrir impressão</a>
          <a id="openJsonBtn" class="btn" href="#" target="_blank" rel="noopener noreferrer">Ver JSON</a>
          <button id="printBtn" class="btn">Imprimir / Baixar PDF</button>
        </div>

        <p class="muted" style="margin-top: 14px;">
          A opção “Imprimir / Baixar PDF” usa a funcionalidade padrão do navegador.
        </p>
      </div>
    </div>
  </div>

  <script>
    const receiptCodeInput = document.getElementById("receiptCode");
    const searchBtn = document.getElementById("searchBtn");
    const errorBox = document.getElementById("errorBox");
    const resultBox = document.getElementById("resultBox");
    const receiptCodeBox = document.getElementById("receiptCodeBox");

    const orderIdEl = document.getElementById("orderId");
    const documentTypeEl = document.getElementById("documentType");
    const channelEl = document.getElementById("channel");
    const regionEl = document.getElementById("region");
    const amountEl = document.getElementById("amount");
    const paymentMethodEl = document.getElementById("paymentMethod");
    const gatewayTransactionIdEl = document.getElementById("gatewayTransactionId");
    const skuIdEl = document.getElementById("skuId");
    const totemIdEl = document.getElementById("totemId");
    const allocationIdEl = document.getElementById("allocationId");
    const pickupIdEl = document.getElementById("pickupId");
    const lockerIdEl = document.getElementById("lockerId");
    const machineIdEl = document.getElementById("machineId");
    const slotEl = document.getElementById("slot");

    const openPrintBtn = document.getElementById("openPrintBtn");
    const openJsonBtn = document.getElementById("openJsonBtn");
    const printBtn = document.getElementById("printBtn");

    function normalizeCode(value) {
      return String(value || "").trim().toUpperCase();
    }

    function setText(el, value) {
      el.textContent = value ?? "";
    }

    function hideError() {
      errorBox.classList.add("hidden");
      errorBox.textContent = "";
    }

    function showError(message) {
      errorBox.textContent = message;
      errorBox.classList.remove("hidden");
    }

    function hideResult() {
      resultBox.classList.add("hidden");
    }

    function showResult() {
      resultBox.classList.remove("hidden");
    }

    async function searchReceipt() {
      hideError();
      hideResult();

      const code = normalizeCode(receiptCodeInput.value);
      receiptCodeInput.value = code;

      if (!code) {
        showError("Informe um código de comprovante.");
        return;
      }

      try {
        const response = await fetch(`/public/fiscal/by-code/${encodeURIComponent(code)}`, {
          method: "GET",
          headers: {
            "Accept": "application/json"
          }
        });

        const data = await response.json();

        if (!response.ok) {
          const message =
            data?.detail?.message ||
            data?.detail ||
            "Não foi possível localizar o comprovante.";
          showError(message);
          return;
        }

        const documentData = data.document || {};
        const orderData = data.order || {};
        const allocationData = data.allocation || {};
        const pickupData = data.pickup || {};
        const links = data.links || {};

        receiptCodeBox.textContent = data.receipt_code || code;
        setText(orderIdEl, orderData.id);
        setText(documentTypeEl, documentData.document_type);
        setText(channelEl, orderData.channel || documentData.channel);
        setText(regionEl, orderData.region || documentData.region);

        const amountCents = Number(documentData.amount_cents || orderData.amount_cents || 0);
        const currency = documentData.currency || "BRL";
        setText(amountEl, `${currency} ${(amountCents / 100).toFixed(2)}`);

        setText(paymentMethodEl, orderData.payment_method);
        setText(gatewayTransactionIdEl, orderData.gateway_transaction_id);
        setText(skuIdEl, orderData.sku_id);
        setText(totemIdEl, orderData.totem_id);
        setText(allocationIdEl, allocationData.id);
        setText(pickupIdEl, pickupData.id);
        setText(lockerIdEl, pickupData.locker_id || allocationData.locker_id);
        setText(machineIdEl, pickupData.machine_id);
        setText(slotEl, pickupData.slot || allocationData.slot);

        openPrintBtn.href = links.print_html || `/public/fiscal/print/${encodeURIComponent(code)}`;
        openJsonBtn.href = links.json || `/public/fiscal/by-code/${encodeURIComponent(code)}`;

        printBtn.onclick = () => {
          window.open(openPrintBtn.href, "_blank", "noopener,noreferrer");
        };

        showResult();
      } catch (error) {
        showError("Erro ao consultar o comprovante.");
      }
    }

    searchBtn.addEventListener("click", searchReceipt);

    receiptCodeInput.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        searchReceipt();
      }
    });
  </script>
</body>
</html>
"""


@router.get("/search", response_class=HTMLResponse)
def public_fiscal_search():
    return HTMLResponse(content=_build_search_html(), status_code=200)


@router.get("/by-code/{receipt_code}")
def public_fiscal_by_code(
    receipt_code: str,
    db: Session = Depends(get_db),
):
    """
    Código de comprovante do stub local (fiscal_documents.receipt_code).
    Para chave de invoice do billing, use order_id + GET público de pedido ou
    expansão futura de lookup no billing.
    """
    normalized_code = _normalize_receipt_code(receipt_code)

    doc = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.receipt_code == normalized_code)
        .first()
    )

    if not doc:
        billing_inv = fetch_invoice_by_receipt_code(normalized_code)
        if billing_inv:
            billing_doc = fiscal_read_view_from_billing_invoice(billing_inv)
            return JSONResponse(content=_serialize_fiscal_document(billing_doc), status_code=200)
        raise HTTPException(
            status_code=404,
            detail={
                "type": "FISCAL_DOCUMENT_NOT_FOUND",
                "message": "Comprovante fiscal não encontrado.",
                "receipt_code": normalized_code,
            },
        )

    return JSONResponse(content=_serialize_fiscal_document(doc), status_code=200)


@router.get("/print/{receipt_code}", response_class=HTMLResponse)
def public_fiscal_print(
    receipt_code: str,
    db: Session = Depends(get_db),
):
    normalized_code = _normalize_receipt_code(receipt_code)

    doc = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.receipt_code == normalized_code)
        .first()
    )

    if not doc:
        billing_inv = fetch_invoice_by_receipt_code(normalized_code)
        if billing_inv:
            billing_doc = fiscal_read_view_from_billing_invoice(billing_inv)
            return HTMLResponse(content=_build_print_html(billing_doc), status_code=200)
        raise HTTPException(
            status_code=404,
            detail={
                "type": "FISCAL_DOCUMENT_NOT_FOUND",
                "message": "Comprovante fiscal não encontrado.",
                "receipt_code": normalized_code,
            },
        )

    return HTMLResponse(content=_build_print_html(doc), status_code=200)

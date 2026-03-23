# 01_source/order_pickup_service/app/routers/public_fiscal.py
from __future__ import annotations

from html import escape

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.fiscal_document import FiscalDocument

router = APIRouter(prefix="/public/fiscal", tags=["public-fiscal"])


def _build_print_html(doc: FiscalDocument) -> str:
    payload = doc.payload_json or {}

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
      --bg: #ffffff;
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
      max-width: 760px;
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
      width: 220px;
      color: var(--muted);
    }}
    .footer {{
      margin-top: 24px;
      font-size: 12px;
      color: var(--muted);
      line-height: 1.5;
    }}
    @media print {{
      body {{
        background: #fff;
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

      <div class="footer">
        Este documento é uma representação simulada persistida localmente para auditoria e impressão.
        A emissão fiscal oficial continua sendo responsabilidade do fluxo fiscal oficial do sistema.
      </div>
    </div>
  </div>
</body>
</html>
"""


@router.get("/print/{receipt_code}", response_class=HTMLResponse)
def public_fiscal_print(
    receipt_code: str,
    db: Session = Depends(get_db),
):
    normalized_code = str(receipt_code or "").strip().upper()
    if not normalized_code:
        raise HTTPException(status_code=400, detail="receipt_code is required")

    doc = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.receipt_code == normalized_code)
        .first()
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "FISCAL_DOCUMENT_NOT_FOUND",
                "message": "Comprovante fiscal não encontrado.",
                "receipt_code": normalized_code,
            },
        )

    return HTMLResponse(content=_build_print_html(doc), status_code=200)

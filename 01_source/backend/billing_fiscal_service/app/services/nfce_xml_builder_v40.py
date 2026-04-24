from __future__ import annotations

from datetime import datetime, timezone
from xml.sax.saxutils import escape

from app.models.invoice_model import Invoice


def _digits_only(value: str | None) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_nfce_xml_v40_stub(
    invoice: Invoice,
    *,
    access_key: str,
    invoice_number: str,
    invoice_series: str,
) -> dict:
    """
    F-3 scaffold: builder NFC-e v4.00 (estrutura mínima com pontos de assinatura A1).
    Ainda não executa assinatura criptográfica; apenas reserva os anchors.
    """
    cnpj = _digits_only(invoice.emitter_cnpj) or "00000000000000"
    cpf = _digits_only(invoice.consumer_cpf)
    amount = (int(invoice.amount_cents or 0)) / 100
    now_iso = _utc_now_iso()

    inf_id = f"NFe{escape(access_key)}"
    xnome_dest = escape(invoice.consumer_name or "CONSUMIDOR FINAL")
    xnome_emit = escape(invoice.emitter_name or "ELLAN EMISSAO STUB")
    cprod = escape(str((invoice.order_snapshot or {}).get("order", {}).get("sku_id") or "SKU-STUB"))
    vprod = f"{amount:.2f}"
    vnf = f"{amount:.2f}"
    cpf_xml = f"<CPF>{cpf}</CPF>" if cpf else ""

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<NFe xmlns="http://www.portalfiscal.inf.br/nfe">'
        f'<infNFe versao="4.00" Id="{inf_id}">'
        "<ide>"
        "<cUF>35</cUF><cNF>00000001</cNF><natOp>VENDA</natOp><mod>65</mod>"
        f"<serie>{escape(invoice_series)}</serie><nNF>{escape(invoice_number)}</nNF>"
        f"<dhEmi>{escape(now_iso)}</dhEmi><tpNF>1</tpNF><idDest>1</idDest>"
        "<tpImp>4</tpImp><tpEmis>1</tpEmis><cDV>0</cDV><tpAmb>2</tpAmb>"
        "<finNFe>1</finNFe><indFinal>1</indFinal><indPres>1</indPres><procEmi>0</procEmi><verProc>ELLAN-F3-STUB</verProc>"
        "</ide>"
        f"<emit><CNPJ>{cnpj}</CNPJ><xNome>{xnome_emit}</xNome><CRT>1</CRT></emit>"
        f"<dest>{cpf_xml}<xNome>{xnome_dest}</xNome><indIEDest>9</indIEDest></dest>"
        "<det nItem=\"1\"><prod>"
        f"<cProd>{cprod}</cProd><xProd>Item</xProd><NCM>00000000</NCM><CFOP>5102</CFOP><uCom>UN</uCom><qCom>1.0000</qCom><vUnCom>{vprod}</vUnCom><vProd>{vprod}</vProd>"
        "<uTrib>UN</uTrib><qTrib>1.0000</qTrib><vUnTrib>"
        f"{vprod}</vUnTrib><indTot>1</indTot>"
        "</prod></det>"
        "<total><ICMSTot>"
        f"<vProd>{vprod}</vProd><vNF>{vnf}</vNF>"
        "</ICMSTot></total>"
        "<transp><modFrete>9</modFrete></transp>"
        "<pag><detPag><tPag>99</tPag><vPag>"
        f"{vnf}</vPag></detPag></pag>"
        "</infNFe>"
        "</NFe>"
    )

    return {
        "format": "nfce_xml_v4_stub",
        "schema_version": "4.00",
        "xml_preview": xml,
        "signature": {
            "mode": "A1_STUB_PENDING",
            "digest_algorithm": "sha256",
            "signature_algorithm": "rsa-sha256",
            "canonicalization": "http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
            "signature_anchor_xpath": "/*[local-name()='NFe']/*[local-name()='infNFe']",
            "signed_info_anchor": "infNFe@Id",
        },
    }

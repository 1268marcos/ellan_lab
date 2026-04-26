import React, { useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

export default function OpsProductsAssetsPage() {
  const { token } = useAuth();
  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);
  const [productId, setProductId] = useState("");
  const [mediaPayload, setMediaPayload] = useState('{\n  "media_type": "IMAGE",\n  "url": "https://cdn.exemplo/item.jpg",\n  "is_primary": true\n}');
  const [barcodePayload, setBarcodePayload] = useState('{\n  "barcode_type": "EAN13",\n  "barcode_value": "7890000000001",\n  "is_primary": true\n}');
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState("");

  async function run(method, endpoint, body, action) {
    if (!token) return;
    setLoading(action);
    try {
      const response = await fetch(`${ORDER_PICKUP_BASE}${endpoint}`, {
        method,
        headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.detail?.message || data?.detail?.type || data?.detail || "falha operacional");
      }
      setResult(JSON.stringify(data, null, 2));
    } catch (err) {
      setResult(`Erro: ${String(err?.message || err || "falha desconhecida")}`);
    } finally {
      setLoading("");
    }
  }

  async function handlePostMedia() {
    const pid = String(productId || "").trim();
    if (!pid) return setResult("Informe product_id.");
    let payload = {};
    try {
      payload = JSON.parse(mediaPayload || "{}");
    } catch (_) {
      return setResult("JSON inválido para media.");
    }
    await run("POST", `/products/${encodeURIComponent(pid)}/media`, payload, "post-media");
  }

  async function handleListMedia() {
    const pid = String(productId || "").trim();
    if (!pid) return setResult("Informe product_id.");
    await run("GET", `/products/${encodeURIComponent(pid)}/media?limit=100`, null, "get-media");
  }

  async function handlePostBarcode() {
    const pid = String(productId || "").trim();
    if (!pid) return setResult("Informe product_id.");
    let payload = {};
    try {
      payload = JSON.parse(barcodePayload || "{}");
    } catch (_) {
      return setResult("JSON inválido para barcode.");
    }
    await run("POST", `/products/${encodeURIComponent(pid)}/barcodes`, payload, "post-barcode");
  }

  async function handleListBarcodes() {
    const pid = String(productId || "").trim();
    if (!pid) return setResult("Informe product_id.");
    await run("GET", `/products/${encodeURIComponent(pid)}/barcodes?limit=100`, null, "get-barcodes");
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>OPS - Products Assets (Pr-1)</h1>
        <p style={mutedStyle}>Operação mínima para media/barcodes por produto.</p>

        <label style={labelStyle}>
          Product ID
          <input value={productId} onChange={(e) => setProductId(e.target.value)} style={inputStyle} placeholder="ex.: sku_123" />
        </label>

        <label style={{ ...labelStyle, marginTop: 10 }}>
          Payload media (JSON)
          <textarea value={mediaPayload} onChange={(e) => setMediaPayload(e.target.value)} style={textareaStyle} />
        </label>
        <div style={actionsStyle}>
          <button type="button" style={buttonStyle} onClick={() => void handlePostMedia()} disabled={Boolean(loading)}>
            {loading === "post-media" ? "Salvando..." : "POST media"}
          </button>
          <button type="button" style={buttonSecondaryStyle} onClick={() => void handleListMedia()} disabled={Boolean(loading)}>
            {loading === "get-media" ? "Consultando..." : "GET media"}
          </button>
        </div>

        <label style={{ ...labelStyle, marginTop: 10 }}>
          Payload barcode (JSON)
          <textarea value={barcodePayload} onChange={(e) => setBarcodePayload(e.target.value)} style={textareaStyle} />
        </label>
        <div style={actionsStyle}>
          <button type="button" style={buttonStyle} onClick={() => void handlePostBarcode()} disabled={Boolean(loading)}>
            {loading === "post-barcode" ? "Salvando..." : "POST barcode"}
          </button>
          <button type="button" style={buttonSecondaryStyle} onClick={() => void handleListBarcodes()} disabled={Boolean(loading)}>
            {loading === "get-barcodes" ? "Consultando..." : "GET barcodes"}
          </button>
        </div>

        <pre style={resultStyle}>{result || "Execute uma ação para visualizar resposta técnica."}</pre>
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8" };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#020617", color: "#E2E8F0" };
const textareaStyle = { minHeight: 110, padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#020617", color: "#E2E8F0", fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace" };
const actionsStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 };
const buttonStyle = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const buttonSecondaryStyle = { padding: "10px 14px", borderRadius: 10, border: "1px solid #334155", background: "#0B1220", color: "#E2E8F0", fontWeight: 700, cursor: "pointer" };
const resultStyle = { marginTop: 12, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 12, overflow: "auto", fontSize: 12, whiteSpace: "pre-wrap" };

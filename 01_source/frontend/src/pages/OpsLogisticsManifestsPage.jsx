import React, { useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

function parseError(payload, fallback = "Nao foi possivel executar a operacao de manifestos.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) return payload.detail.message.trim();
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) return payload.detail.type.trim();
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

export default function OpsLogisticsManifestsPage() {
  const { token } = useAuth();
  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  const [manifestId, setManifestId] = useState("");
  const [itemId, setItemId] = useState("");
  const [exceptionReason, setExceptionReason] = useState("etiqueta ilegivel no recebimento");
  const [closePayload, setClosePayload] = useState('{\n  "actual_parcel_count": 0,\n  "carrier_note": "fechamento operacional D2"\n}');
  const [result, setResult] = useState("");
  const [loadingAction, setLoadingAction] = useState("");

  async function runAction({ endpoint, method, body, successLabel }) {
    if (!token) return;
    setLoadingAction(successLabel);
    try {
      const response = await fetch(`${ORDER_PICKUP_BASE}${endpoint}`, {
        method,
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseError(data));
      }
      setResult(JSON.stringify(data, null, 2));
    } catch (err) {
      setResult(`Erro: ${String(err?.message || err || "falha desconhecida")}`);
    } finally {
      setLoadingAction("");
    }
  }

  async function handleListItems() {
    const id = String(manifestId || "").trim();
    if (!id) {
      setResult("Informe manifest_id para listar itens.");
      return;
    }
    await runAction({
      endpoint: `/logistics/manifests/${encodeURIComponent(id)}/items?limit=200&offset=0`,
      method: "GET",
      successLabel: "list-items",
    });
  }

  async function handleCloseManifest() {
    const id = String(manifestId || "").trim();
    if (!id) {
      setResult("Informe manifest_id para fechar manifesto.");
      return;
    }
    let parsedBody = {};
    try {
      parsedBody = JSON.parse(closePayload || "{}");
    } catch (_) {
      setResult("JSON de fechamento invalido.");
      return;
    }
    await runAction({
      endpoint: `/logistics/manifests/${encodeURIComponent(id)}/close`,
      method: "POST",
      body: parsedBody,
      successLabel: "close-manifest",
    });
  }

  async function handleMarkException() {
    const id = String(manifestId || "").trim();
    const normalizedItemId = Number(itemId || 0);
    const reason = String(exceptionReason || "").trim();
    if (!id || !Number.isFinite(normalizedItemId) || normalizedItemId <= 0 || !reason) {
      setResult("Informe manifest_id, item_id e reason para registrar exception.");
      return;
    }
    await runAction({
      endpoint: `/logistics/manifests/${encodeURIComponent(id)}/items/${normalizedItemId}/exception`,
      method: "POST",
      body: { reason },
      successLabel: "mark-exception",
    });
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>OPS - Logistics Manifests (D2)</h1>
        <p style={mutedStyle}>
          Operação rápida para endpoints D2 de manifesto: listar itens, fechar manifesto e registrar exception idempotente.
        </p>

        <div style={gridStyle}>
          <label style={labelStyle}>
            Manifest ID
            <input value={manifestId} onChange={(e) => setManifestId(e.target.value)} placeholder="ex.: a9f8d0a6-..." style={inputStyle} />
          </label>
          <label style={labelStyle}>
            Item ID (exception)
            <input value={itemId} onChange={(e) => setItemId(e.target.value)} placeholder="ex.: 101" style={inputStyle} />
          </label>
        </div>

        <label style={{ ...labelStyle, marginTop: 10 }}>
          Reason (exception)
          <input value={exceptionReason} onChange={(e) => setExceptionReason(e.target.value)} style={inputStyle} />
        </label>

        <label style={{ ...labelStyle, marginTop: 10 }}>
          Payload close (JSON)
          <textarea value={closePayload} onChange={(e) => setClosePayload(e.target.value)} style={textareaStyle} />
        </label>

        <div style={actionsStyle}>
          <button type="button" onClick={() => void handleListItems()} style={buttonStyle} disabled={Boolean(loadingAction)}>
            {loadingAction === "list-items" ? "Listando..." : "GET items"}
          </button>
          <button type="button" onClick={() => void handleCloseManifest()} style={buttonStyle} disabled={Boolean(loadingAction)}>
            {loadingAction === "close-manifest" ? "Fechando..." : "POST close"}
          </button>
          <button type="button" onClick={() => void handleMarkException()} style={buttonStyle} disabled={Boolean(loadingAction)}>
            {loadingAction === "mark-exception" ? "Marcando..." : "POST exception"}
          </button>
        </div>

        <pre style={resultStyle}>{result || "Execute uma acao para visualizar resposta tecnica."}</pre>
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8", marginTop: 8 };
const gridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const textareaStyle = { minHeight: 120, padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0", fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace" };
const actionsStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 };
const buttonStyle = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const resultStyle = { marginTop: 12, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 12, overflow: "auto", fontSize: 12, whiteSpace: "pre-wrap" };

import React, { useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsActionButton from "../components/OpsActionButton";
import OpsScenarioPresets from "../components/OpsScenarioPresets";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

function parseError(payload, fallback = "Falha ao consultar partner lookup.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) return payload.detail.message.trim();
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) return payload.detail.type.trim();
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

export default function OpsIntegrationOrdersPartnerLookupPage() {
  const { token } = useAuth();
  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  const [partnerId, setPartnerId] = useState("partner_demo_001");
  const [partnerOrderRef, setPartnerOrderRef] = useState("PO-7788");
  const [limit, setLimit] = useState("20");
  const [offset, setOffset] = useState("0");
  const [loading, setLoading] = useState(false);
  const [copyStatus, setCopyStatus] = useState("");
  const [result, setResult] = useState("");

  function applyPreset(preset) {
    if (preset === "success") {
      setPartnerId("partner_demo_001");
      setPartnerOrderRef("PO-7788");
      setLimit("20");
      setOffset("0");
      return;
    }
    if (preset === "bulk") {
      setPartnerId("partner_demo_001");
      setPartnerOrderRef("");
      setLimit("50");
      setOffset("0");
      return;
    }
    setPartnerId("partner_invalido");
    setPartnerOrderRef("SEM_MATCH");
    setLimit("20");
    setOffset("0");
  }

  async function handleLookup() {
    if (!token) return;
    const normalizedPartnerId = String(partnerId || "").trim();
    if (!normalizedPartnerId) {
      setResult("Informe partner_id.");
      return;
    }

    const params = new URLSearchParams();
    params.set("partner_id", normalizedPartnerId);
    const normalizedRef = String(partnerOrderRef || "").trim();
    if (normalizedRef) params.set("partner_order_ref", normalizedRef);
    params.set("limit", String(Number(limit || 20) || 20));
    params.set("offset", String(Number(offset || 0) || 0));

    setLoading(true);
    try {
      const response = await fetch(`${ORDER_PICKUP_BASE}/orders/partner-lookup?${params.toString()}`, {
        method: "GET",
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));
      setResult(JSON.stringify(data, null, 2));
    } catch (err) {
      setResult(`Erro: ${String(err?.message || err || "erro desconhecido")}`);
    } finally {
      setLoading(false);
    }
  }

  function buildEvidenceSummary() {
    const lines = [
      "L-3 Orders Integration Evidence Snapshot",
      `timestamp: ${new Date().toISOString()}`,
      `partner_id: ${String(partnerId || "").trim() || "(não informado)"}`,
      `partner_order_ref: ${String(partnerOrderRef || "").trim() || "-"}`,
      `limit: ${String(limit || "").trim() || "20"}`,
      `offset: ${String(offset || "").trim() || "0"}`,
    ];
    if (String(result || "").trim()) {
      lines.push("", "payload_snippet_500:");
      lines.push(String(result).replace(/\s+/g, " ").slice(0, 500));
    }
    return lines.join("\n");
  }

  async function handleCopyEvidence() {
    const summary = buildEvidenceSummary();
    try {
      await navigator.clipboard.writeText(summary);
      setCopyStatus("Resumo de evidência copiado para a área de transferência.");
      window.setTimeout(() => setCopyStatus(""), 2200);
    } catch (_) {
      setCopyStatus("Falha ao copiar automaticamente. Copie manualmente do painel técnico.");
    }
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>OPS - Orders Partner Lookup (L-3)</h1>
        <p style={mutedStyle}>
          Guia rápido: 1) informar <b>partner_id</b>; 2) opcionalmente filtrar por <b>partner_order_ref</b>; 3) executar lookup e copiar evidência.
        </p>

        <div style={filtersStyle}>
          <label style={labelStyle}>
            partner_id
            <input value={partnerId} onChange={(e) => setPartnerId(e.target.value)} style={inputStyle} placeholder="partner_demo_001" />
          </label>
          <label style={labelStyle}>
            partner_order_ref (opcional)
            <input value={partnerOrderRef} onChange={(e) => setPartnerOrderRef(e.target.value)} style={inputStyle} placeholder="PO-7788" />
          </label>
          <label style={labelStyle}>
            limit
            <input value={limit} onChange={(e) => setLimit(e.target.value)} style={inputStyle} />
          </label>
          <label style={labelStyle}>
            offset
            <input value={offset} onChange={(e) => setOffset(e.target.value)} style={inputStyle} />
          </label>
        </div>

        <OpsScenarioPresets
          style={{ marginBottom: 10 }}
          disabled={loading}
          items={[
            { id: "success", tone: "success", label: "Preset verde: match esperado", onClick: () => applyPreset("success") },
            { id: "bulk", tone: "warn", label: "Preset âmbar: varredura por partner", onClick: () => applyPreset("bulk") },
            { id: "error", tone: "error", label: "Preset vermelho: erro controlado", onClick: () => applyPreset("error") },
          ]}
        />

        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleLookup()} disabled={loading}>
            {loading ? "Consultando..." : "GET partner-lookup"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="copy" onClick={() => void handleCopyEvidence()} disabled={loading}>
            Copiar evidência
          </OpsActionButton>
        </div>
        {copyStatus ? <div style={copyStatusStyle}>{copyStatus}</div> : null}

        <pre style={resultStyle}>{result || "Execute o lookup para visualizar resposta técnica."}</pre>
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif", display: "grid", gap: 12 };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8" };
const filtersStyle = { display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", marginBottom: 10 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#020617", color: "#E2E8F0" };
const actionsStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 };
const copyStatusStyle = { marginTop: 8, fontSize: 12, color: "#93C5FD" };
const resultStyle = { marginTop: 12, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 12, overflow: "auto", fontSize: 12, whiteSpace: "pre-wrap" };

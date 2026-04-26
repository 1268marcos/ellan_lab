import React, { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsActionButton from "../components/OpsActionButton";
import OpsScenarioPresets from "../components/OpsScenarioPresets";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const STORAGE_KEY = "ops_integration_orders_fiscal_actions_v1";

const ACTIONS = [
  { key: "fulfillment", label: "GET fulfillment" },
  { key: "partnerEvents", label: "GET partner-events" },
  { key: "retryEvent", label: "POST partner-events/retry" },
  { key: "fiscalLogByOrder", label: "GET fiscal log by order" },
  { key: "fiscalReprocess", label: "POST fiscal reprocess" },
];

function defaultActionStatus() {
  const nowIso = new Date().toISOString();
  return ACTIONS.reduce((acc, item) => {
    acc[item.key] = { status: "idle", note: "Aguardando execução", updatedAt: nowIso };
    return acc;
  }, {});
}

function parseError(payload, fallback = "Falha operacional.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) return payload.detail.message.trim();
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) return payload.detail.type.trim();
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

function ActionChip({ label, state }) {
  const tone = state?.status === "success" ? chipSuccessStyle : state?.status === "error" ? chipErrorStyle : state?.status === "running" ? chipRunningStyle : chipIdleStyle;
  return (
    <article style={{ ...chipBaseStyle, ...tone }}>
      <strong style={{ fontSize: 12 }}>{label}</strong>
      <small style={{ fontSize: 11 }}>{state?.note || "-"}</small>
      <small style={{ fontSize: 10, opacity: 0.9 }}>{state?.updatedAt ? new Date(state.updatedAt).toLocaleString() : "-"}</small>
    </article>
  );
}

export default function OpsIntegrationOrdersFiscalPage() {
  const { token } = useAuth();
  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  const [orderId, setOrderId] = useState("order_i1_001");
  const [outboxId, setOutboxId] = useState("");
  const [forceRetry, setForceRetry] = useState(false);
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState("");
  const [actionStatus, setActionStatus] = useState(defaultActionStatus);
  const [copyStatus, setCopyStatus] = useState("");

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === "object") setActionStatus((prev) => ({ ...prev, ...parsed }));
    } catch (_) {
      // no-op
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(actionStatus));
    } catch (_) {
      // no-op
    }
  }, [actionStatus]);

  function setAction(key, status, note) {
    setActionStatus((prev) => ({
      ...prev,
      [key]: { status, note, updatedAt: new Date().toISOString() },
    }));
  }

  async function run({ actionKey, method, endpoint }) {
    if (!token) return null;
    setLoading(actionKey);
    setAction(actionKey, "running", "Executando...");
    try {
      const response = await fetch(`${ORDER_PICKUP_BASE}${endpoint}`, {
        method,
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));
      setResult(JSON.stringify(data, null, 2));
      setAction(actionKey, "success", "Sucesso");
      return data;
    } catch (err) {
      const message = String(err?.message || err || "erro desconhecido");
      setResult(`Erro: ${message}`);
      setAction(actionKey, "error", message);
      return null;
    } finally {
      setLoading("");
    }
  }

  function getNormalizedOrderId() {
    return String(orderId || "").trim();
  }

  function applyPreset(preset) {
    if (preset === "success") {
      setOrderId("order_i1_001");
      setOutboxId("");
      setForceRetry(false);
      return;
    }
    if (preset === "retry") {
      setOrderId("order_i1_001");
      setOutboxId("");
      setForceRetry(true);
      return;
    }
    setOrderId("order_i1_default_fallback");
    setOutboxId("");
    setForceRetry(false);
  }

  function buildEvidenceSummary() {
    const normalizedOrderId = getNormalizedOrderId() || "(não informado)";
    const ts = new Date().toISOString();
    const executed = ACTIONS.filter((item) => actionStatus[item.key]?.status && actionStatus[item.key]?.status !== "idle");
    const lines = [
      `I-1 OPS Evidence Snapshot`,
      `timestamp: ${ts}`,
      `order_id: ${normalizedOrderId}`,
      `outbox_id: ${String(outboxId || "").trim() || "-"}`,
      `force_retry: ${String(Boolean(forceRetry))}`,
      `actions_executed: ${executed.length}`,
      "",
      "status_by_chip:",
      ...(executed.length
        ? executed.map((item) => {
            const state = actionStatus[item.key] || {};
            return `- ${item.label}: status=${state.status || "unknown"}; note=${state.note || "-"}; updated_at=${state.updatedAt || "-"}`;
          })
        : ["- nenhuma ação executada ainda"]),
    ];
    const payloadSnippet = String(result || "").trim();
    if (payloadSnippet) {
      const normalizedSnippet = payloadSnippet.replace(/\s+/g, " ").slice(0, 500);
      lines.push("", "payload_snippet_500:", normalizedSnippet);
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

  async function handleGetFulfillment() {
    const oid = getNormalizedOrderId();
    if (!oid) return setResult("Informe order_id.");
    await run({ actionKey: "fulfillment", method: "GET", endpoint: `/orders/${encodeURIComponent(oid)}/fulfillment` });
  }

  async function handleGetPartnerEvents() {
    const oid = getNormalizedOrderId();
    if (!oid) return setResult("Informe order_id.");
    await run({ actionKey: "partnerEvents", method: "GET", endpoint: `/orders/${encodeURIComponent(oid)}/partner-events?limit=50` });
  }

  async function handleRetryPartnerEvent() {
    const oid = getNormalizedOrderId();
    if (!oid) return setResult("Informe order_id.");
    const params = new URLSearchParams();
    params.set("force", String(Boolean(forceRetry)));
    if (String(outboxId || "").trim()) params.set("outbox_id", String(outboxId).trim());
    await run({
      actionKey: "retryEvent",
      method: "POST",
      endpoint: `/orders/${encodeURIComponent(oid)}/partner-events/retry?${params.toString()}`,
    });
  }

  async function handleGetFiscalLogByOrder() {
    const oid = getNormalizedOrderId();
    if (!oid) return setResult("Informe order_id.");
    await run({ actionKey: "fiscalLogByOrder", method: "GET", endpoint: `/fiscal/auto-classification-log/${encodeURIComponent(oid)}?limit=100` });
  }

  async function handleFiscalReprocess() {
    const oid = getNormalizedOrderId();
    if (!oid) return setResult("Informe order_id.");
    await run({ actionKey: "fiscalReprocess", method: "POST", endpoint: `/fiscal/auto-classification/${encodeURIComponent(oid)}/reprocess` });
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>OPS - Integration Orders/Fiscal (I-1)</h1>
        <p style={mutedStyle}>Guia rápido: 1) consultar fulfillment; 2) inspecionar/retry de partner-events; 3) consultar/reprocessar classificação fiscal por pedido.</p>

        <div style={filtersStyle}>
          <label style={labelStyle}>
            order_id
            <input value={orderId} onChange={(e) => setOrderId(e.target.value)} style={inputStyle} placeholder="order_i1_001" />
          </label>
          <label style={labelStyle}>
            outbox_id (opcional no retry)
            <input value={outboxId} onChange={(e) => setOutboxId(e.target.value)} style={inputStyle} placeholder="poeo_xxx" />
          </label>
          <label style={toggleLabelStyle}>
            <input type="checkbox" checked={forceRetry} onChange={(e) => setForceRetry(e.target.checked)} />
            force retry (permitir DELIVERED)
          </label>
        </div>

        <OpsScenarioPresets
          style={presetRowStyle}
          disabled={Boolean(loading)}
          items={[
            { id: "success", tone: "success", label: "Preset verde: cenário sucesso", onClick: () => applyPreset("success") },
            { id: "retry", tone: "warn", label: "Preset âmbar: cenário retry", onClick: () => applyPreset("retry") },
            { id: "default", tone: "error", label: "Preset vermelho: diagnóstico fiscal", onClick: () => applyPreset("default") },
          ]}
        />

        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleGetFulfillment()} disabled={Boolean(loading)}>
            {loading === "fulfillment" ? "Carregando..." : "GET fulfillment"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="secondary" onClick={() => void handleGetPartnerEvents()} disabled={Boolean(loading)}>
            {loading === "partnerEvents" ? "Carregando..." : "GET partner-events"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="warn" onClick={() => void handleRetryPartnerEvent()} disabled={Boolean(loading)}>
            {loading === "retryEvent" ? "Executando..." : "POST retry event"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="secondary" onClick={() => void handleGetFiscalLogByOrder()} disabled={Boolean(loading)}>
            {loading === "fiscalLogByOrder" ? "Carregando..." : "GET fiscal log by order"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleFiscalReprocess()} disabled={Boolean(loading)}>
            {loading === "fiscalReprocess" ? "Reprocessando..." : "POST fiscal reprocess"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="copy" onClick={() => void handleCopyEvidence()} disabled={Boolean(loading)}>
            Copiar evidência
          </OpsActionButton>
        </div>
        {copyStatus ? <div style={copyStatusStyle}>{copyStatus}</div> : null}

        <div style={chipsGridStyle}>
          {ACTIONS.map((item) => (
            <ActionChip key={item.key} label={item.label} state={actionStatus[item.key]} />
          ))}
        </div>

        <pre style={resultStyle}>{result || "Execute uma ação para visualizar resposta técnica."}</pre>
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
const toggleLabelStyle = { color: "#CBD5E1", fontSize: 12, display: "flex", alignItems: "center", gap: 6, paddingTop: 24 };
const actionsStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 };
const presetRowStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 };
const copyStatusStyle = { marginTop: 8, fontSize: 12, color: "#93C5FD" };
const resultStyle = { marginTop: 12, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 12, overflow: "auto", fontSize: 12, whiteSpace: "pre-wrap" };
const chipsGridStyle = { display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", marginTop: 10 };
const chipBaseStyle = { borderRadius: 10, border: "1px solid #334155", padding: "8px 10px", display: "grid", gap: 2 };
const chipIdleStyle = { background: "#0B1220", color: "#CBD5E1" };
const chipRunningStyle = { background: "rgba(217,119,6,0.2)", border: "1px solid rgba(217,119,6,0.45)", color: "#FDE68A" };
const chipSuccessStyle = { background: "rgba(22,163,74,0.2)", border: "1px solid rgba(22,163,74,0.45)", color: "#86EFAC" };
const chipErrorStyle = { background: "rgba(220,38,38,0.18)", border: "1px solid rgba(220,38,38,0.45)", color: "#FCA5A5" };

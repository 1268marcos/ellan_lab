import React, { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsActionButton from "../components/OpsActionButton";
import OpsScenarioPresets from "../components/OpsScenarioPresets";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const STORAGE_KEY = "ops_partners_financials_service_areas_actions_v1";

const ACTIONS = [
  { key: "listSettlements", label: "GET settlements" },
  { key: "generateSettlement", label: "POST settlements/generate" },
  { key: "approveSettlement", label: "PATCH settlements/approve" },
  { key: "listPerformance", label: "GET performance" },
  { key: "listServiceAreas", label: "GET service-areas" },
  { key: "createServiceArea", label: "POST service-areas" },
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

export default function OpsPartnersFinancialsServiceAreasPage() {
  const { token } = useAuth();
  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  const [partnerId, setPartnerId] = useState("partner_demo_001");
  const [batchId, setBatchId] = useState("");
  const [settlementStatusFilter, setSettlementStatusFilter] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState("");
  const [copyStatus, setCopyStatus] = useState("");
  const [actionStatus, setActionStatus] = useState(defaultActionStatus);

  const [generatePayload, setGeneratePayload] = useState(`{
  "period_start": "2026-04-01",
  "period_end": "2026-04-15",
  "revenue_share_pct": 0.15,
  "fees_cents": 2500,
  "currency": "BRL",
  "notes": "Primeira quinzena"
}`);
  const [approvePayload, setApprovePayload] = useState(`{
  "settlement_ref": "PIX-APR-2026-0001",
  "notes": "Aprovado por operacao"
}`);
  const [serviceAreaPayload, setServiceAreaPayload] = useState(`{
  "locker_id": "locker_sp_001",
  "priority": 50,
  "exclusive": false,
  "valid_from": "2026-04-01",
  "valid_until": "2026-06-30",
  "is_active": true
}`);

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

  function getNormalizedPartnerId() {
    return String(partnerId || "").trim();
  }

  async function run({ actionKey, method, endpoint, body }) {
    if (!token) return null;
    setLoading(actionKey);
    setAction(actionKey, "running", "Executando...");
    try {
      const response = await fetch(`${ORDER_PICKUP_BASE}${endpoint}`, {
        method,
        headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
        body: body ? JSON.stringify(body) : undefined,
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

  function applyPreset(key) {
    if (key === "healthy") {
      setPartnerId("partner_demo_001");
      setBatchId("");
      setSettlementStatusFilter("DRAFT");
      setGeneratePayload(`{
  "period_start": "2026-04-01",
  "period_end": "2026-04-15",
  "revenue_share_pct": 0.12,
  "fees_cents": 1200,
  "currency": "BRL",
  "notes": "Cenario verde"
}`);
      return;
    }
    if (key === "approval") {
      setPartnerId("partner_demo_001");
      setBatchId("batch_to_approve_001");
      setSettlementStatusFilter("DRAFT");
      setApprovePayload(`{
  "settlement_ref": "PIX-APR-OPS-0002",
  "notes": "Aprovacao operacional de rotina"
}`);
      return;
    }
    setPartnerId("partner_demo_critical");
    setBatchId("");
    setSettlementStatusFilter("DISPUTED");
    setServiceAreaPayload(`{
  "locker_id": "locker_sp_critical_001",
  "priority": 10,
  "exclusive": true,
  "valid_from": "2026-04-01",
  "valid_until": null,
  "is_active": true
}`);
  }

  function buildEvidenceSummary() {
    const normalizedPartnerId = getNormalizedPartnerId() || "(nao informado)";
    const ts = new Date().toISOString();
    const executed = ACTIONS.filter((item) => actionStatus[item.key]?.status && actionStatus[item.key]?.status !== "idle");
    const lines = [
      "P-3 OPS Evidence Snapshot",
      `timestamp: ${ts}`,
      `partner_id: ${normalizedPartnerId}`,
      `batch_id: ${String(batchId || "").trim() || "-"}`,
      `status_filter: ${String(settlementStatusFilter || "").trim() || "-"}`,
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

  async function handleListSettlements() {
    const pid = getNormalizedPartnerId();
    if (!pid) return setResult("Informe partner_id.");
    const params = new URLSearchParams();
    if (String(settlementStatusFilter || "").trim()) params.set("status", String(settlementStatusFilter).trim().toUpperCase());
    params.set("limit", "100");
    await run({
      actionKey: "listSettlements",
      method: "GET",
      endpoint: `/partners/${encodeURIComponent(pid)}/settlements?${params.toString()}`,
    });
  }

  async function handleGenerateSettlement() {
    const pid = getNormalizedPartnerId();
    if (!pid) return setResult("Informe partner_id.");
    let payload = {};
    try {
      payload = JSON.parse(generatePayload || "{}");
    } catch (_) {
      setResult("JSON inválido em generate payload.");
      return;
    }
    await run({
      actionKey: "generateSettlement",
      method: "POST",
      endpoint: `/partners/${encodeURIComponent(pid)}/settlements/generate`,
      body: payload,
    });
  }

  async function handleApproveSettlement() {
    const pid = getNormalizedPartnerId();
    const bid = String(batchId || "").trim();
    if (!pid) return setResult("Informe partner_id.");
    if (!bid) return setResult("Informe batch_id para aprovar settlement.");
    let payload = {};
    try {
      payload = JSON.parse(approvePayload || "{}");
    } catch (_) {
      setResult("JSON inválido em approve payload.");
      return;
    }
    await run({
      actionKey: "approveSettlement",
      method: "PATCH",
      endpoint: `/partners/${encodeURIComponent(pid)}/settlements/${encodeURIComponent(bid)}/approve`,
      body: payload,
    });
  }

  async function handleListPerformance() {
    const pid = getNormalizedPartnerId();
    if (!pid) return setResult("Informe partner_id.");
    await run({
      actionKey: "listPerformance",
      method: "GET",
      endpoint: `/partners/${encodeURIComponent(pid)}/performance?limit=6`,
    });
  }

  async function handleListServiceAreas() {
    const pid = getNormalizedPartnerId();
    if (!pid) return setResult("Informe partner_id.");
    await run({
      actionKey: "listServiceAreas",
      method: "GET",
      endpoint: `/partners/${encodeURIComponent(pid)}/service-areas?only_active=true&limit=200`,
    });
  }

  async function handleCreateServiceArea() {
    const pid = getNormalizedPartnerId();
    if (!pid) return setResult("Informe partner_id.");
    let payload = {};
    try {
      payload = JSON.parse(serviceAreaPayload || "{}");
    } catch (_) {
      setResult("JSON inválido em service-area payload.");
      return;
    }
    await run({
      actionKey: "createServiceArea",
      method: "POST",
      endpoint: `/partners/${encodeURIComponent(pid)}/service-areas`,
      body: payload,
    });
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>OPS - Partners Financials & Service Areas (P-3)</h1>
        <p style={mutedStyle}>Guia rápido: 1) listar/gerar settlements; 2) aprovar batch; 3) validar performance e service-areas com rastreio por chips.</p>

        <div style={filtersStyle}>
          <label style={labelStyle}>
            partner_id
            <input value={partnerId} onChange={(e) => setPartnerId(e.target.value)} style={inputStyle} placeholder="partner_demo_001" />
          </label>
          <label style={labelStyle}>
            batch_id (aprovação)
            <input value={batchId} onChange={(e) => setBatchId(e.target.value)} style={inputStyle} placeholder="batch_to_approve_001" />
          </label>
          <label style={labelStyle}>
            settlement status (filtro GET)
            <input value={settlementStatusFilter} onChange={(e) => setSettlementStatusFilter(e.target.value)} style={inputStyle} placeholder="DRAFT | APPROVED | PAID" />
          </label>
        </div>

        <OpsScenarioPresets
          style={presetRowStyle}
          disabled={Boolean(loading)}
          items={[
            { id: "healthy", tone: "success", label: "Preset verde: ciclo saudável", onClick: () => applyPreset("healthy") },
            { id: "approval", tone: "warn", label: "Preset âmbar: aprovação de batch", onClick: () => applyPreset("approval") },
            { id: "risk", tone: "error", label: "Preset vermelho: cobertura crítica", onClick: () => applyPreset("risk") },
          ]}
        />

        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="secondary" onClick={() => void handleListSettlements()} disabled={Boolean(loading)}>
            {loading === "listSettlements" ? "Carregando..." : "GET settlements"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleGenerateSettlement()} disabled={Boolean(loading)}>
            {loading === "generateSettlement" ? "Gerando..." : "POST settlements/generate"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="warn" onClick={() => void handleApproveSettlement()} disabled={Boolean(loading)}>
            {loading === "approveSettlement" ? "Aprovando..." : "PATCH settlements/approve"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="secondary" onClick={() => void handleListPerformance()} disabled={Boolean(loading)}>
            {loading === "listPerformance" ? "Carregando..." : "GET performance"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="secondary" onClick={() => void handleListServiceAreas()} disabled={Boolean(loading)}>
            {loading === "listServiceAreas" ? "Carregando..." : "GET service-areas"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleCreateServiceArea()} disabled={Boolean(loading)}>
            {loading === "createServiceArea" ? "Enviando..." : "POST service-areas"}
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
      </section>

      <section style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>Payloads operacionais</h2>
        <p style={mutedStyle}>Ajuda contextual: ajuste payloads antes de executar mutações. Use os presets para acelerar handoff no plantão.</p>

        <label style={labelStyle}>
          Payload settlement generate (POST /partners/&lt;id&gt;/settlements/generate)
          <textarea value={generatePayload} onChange={(e) => setGeneratePayload(e.target.value)} style={textareaStyle} />
        </label>

        <label style={{ ...labelStyle, marginTop: 10 }}>
          Payload settlement approve (PATCH /partners/&lt;id&gt;/settlements/&lt;batch_id&gt;/approve)
          <textarea value={approvePayload} onChange={(e) => setApprovePayload(e.target.value)} style={textareaStyle} />
        </label>

        <label style={{ ...labelStyle, marginTop: 10 }}>
          Payload service-area create (POST /partners/&lt;id&gt;/service-areas)
          <textarea value={serviceAreaPayload} onChange={(e) => setServiceAreaPayload(e.target.value)} style={textareaStyle} />
        </label>

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
const textareaStyle = { minHeight: 100, padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#020617", color: "#E2E8F0", fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace" };
const actionsStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 };
const presetRowStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 };
const copyStatusStyle = { marginTop: 8, fontSize: 12, color: "#93C5FD" };
const resultStyle = { marginTop: 12, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 12, overflow: "auto", fontSize: 12, whiteSpace: "pre-wrap" };
const chipsGridStyle = { display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", marginTop: 10 };
const chipBaseStyle = { borderRadius: 10, border: "1px solid #334155", padding: "8px 10px", display: "grid", gap: 2 };
const chipIdleStyle = { background: "#0B1220", color: "#CBD5E1" };
const chipRunningStyle = { background: "rgba(217,119,6,0.2)", border: "1px solid rgba(217,119,6,0.45)", color: "#FDE68A" };
const chipSuccessStyle = { background: "rgba(22,163,74,0.2)", border: "1px solid rgba(22,163,74,0.45)", color: "#86EFAC" };
const chipErrorStyle = { background: "rgba(220,38,38,0.18)", border: "1px solid rgba(220,38,38,0.45)", color: "#FCA5A5" };

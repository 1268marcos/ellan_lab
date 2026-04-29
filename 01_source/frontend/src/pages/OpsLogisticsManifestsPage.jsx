import React, { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsActionButton from "../components/OpsActionButton";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import OpsScenarioPresets from "../components/OpsScenarioPresets";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const ACTION_STATUS_STORAGE_KEY = "ops_logistics_manifests:action_status_v1";

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
  const [focusMode, setFocusMode] = useState("inspect");
  const [actionStatus, setActionStatus] = useState({
    "get-items": { status: "idle", at: null, note: "Aguardando execução" },
    "post-close": { status: "idle", at: null, note: "Aguardando execução" },
    "post-exception": { status: "idle", at: null, note: "Aguardando execução" },
  });

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(ACTION_STATUS_STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object") return;
      setActionStatus((prev) => ({
        ...prev,
        "get-items": {
          ...prev["get-items"],
          ...(parsed["get-items"] || {}),
        },
        "post-close": {
          ...prev["post-close"],
          ...(parsed["post-close"] || {}),
        },
        "post-exception": {
          ...prev["post-exception"],
          ...(parsed["post-exception"] || {}),
        },
      }));
    } catch (_) {
      // fallback silencioso em ambientes sem storage/JSON inválido
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(ACTION_STATUS_STORAGE_KEY, JSON.stringify(actionStatus));
    } catch (_) {
      // fallback silencioso para ambiente sem localStorage
    }
  }, [actionStatus]);

  function updateActionStatus(actionKey, status, note) {
    setActionStatus((prev) => ({
      ...prev,
      [actionKey]: {
        status,
        at: new Date().toLocaleTimeString("pt-BR"),
        note,
      },
    }));
  }

  async function runAction({ endpoint, method, body, successLabel, actionKey }) {
    if (!token) return;
    setLoadingAction(successLabel);
    updateActionStatus(actionKey, "running", "Executando...");
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
      updateActionStatus(actionKey, "success", "Executado com sucesso");
    } catch (err) {
      const message = String(err?.message || err || "falha desconhecida");
      setResult(`Erro: ${message}`);
      updateActionStatus(actionKey, "error", message);
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
      actionKey: "get-items",
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
      actionKey: "post-close",
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
      actionKey: "post-exception",
    });
  }

  function applyQuickFlow(mode) {
    setFocusMode(mode);
    setResult("");
    if (mode === "inspect") {
      setExceptionReason("etiqueta ilegivel no recebimento");
      setClosePayload('{\n  "actual_parcel_count": 0,\n  "carrier_note": "fechamento operacional D2"\n}');
      return;
    }
    if (mode === "close") {
      setClosePayload('{\n  "actual_parcel_count": 22,\n  "carrier_note": "fechamento turno manha"\n}');
      return;
    }
    if (mode === "exception") {
      setExceptionReason("etiqueta ilegivel no recebimento");
    }
  }

  const contextGuide = {
    inspect: {
      title: "Inspeção do manifesto",
      objective: "Consultar itens antes de tomar ação operacional.",
      usage: "Preencha manifest_id e execute GET items para confirmar status dos itens.",
    },
    close: {
      title: "Fechamento idempotente",
      objective: "Fechar manifesto com reconciliação expected vs actual.",
      usage: "Ajuste o JSON de close e execute POST close. Reexecuções devem manter estado consolidado.",
    },
    exception: {
      title: "Tratamento de exceção",
      objective: "Marcar item problemático sem quebrar o lote.",
      usage: "Informe item_id e reason; reenvio no mesmo item deve ser idempotente.",
    },
  }[focusMode];

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS - Logistics Manifests (D2)" />
        <p style={mutedStyle}>
          Operação rápida para endpoints D2 de manifesto: listar itens, fechar manifesto e registrar exception idempotente.
        </p>

        <div style={playbookStyle}>
          <h3 style={{ margin: 0 }}>Guia rápido</h3>
          <ol style={playbookListStyle}>
            <li>Inspecione itens do manifesto com <b>GET items</b>.</li>
            <li>Se necessário, marque item com <b>POST exception</b>.</li>
            <li>Finalize com <b>POST close</b> e valide idempotência no replay.</li>
          </ol>
          <OpsScenarioPresets
            style={quickActionsStyle}
            disabled={Boolean(loadingAction)}
            items={[
              { id: "inspect", tone: "success", label: "Preset verde: inspecionar", onClick: () => applyQuickFlow("inspect") },
              { id: "close", tone: "warn", label: "Preset âmbar: fechamento parcial", onClick: () => applyQuickFlow("close") },
              { id: "exception", tone: "error", label: "Preset vermelho: exception crítica", onClick: () => applyQuickFlow("exception") },
            ]}
          />
        </div>

        <div style={contextHelpStyle}>
          <div><b>Contexto atual:</b> {contextGuide.title}</div>
          <div><b>Objetivo:</b> {contextGuide.objective}</div>
          <div><b>Como usar:</b> {contextGuide.usage}</div>
        </div>

        <div style={chipsRowStyle}>
          <ActionChip label="GET items" data={actionStatus["get-items"]} />
          <ActionChip label="POST close" data={actionStatus["post-close"]} />
          <ActionChip label="POST exception" data={actionStatus["post-exception"]} />
        </div>

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
          <div style={presetRowStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => setExceptionReason("etiqueta ilegivel no recebimento")} disabled={Boolean(loadingAction)}>
              Preset: etiqueta ilegível
            </button>
            <button type="button" style={buttonGhostStyle} onClick={() => setExceptionReason("pacote avariado no recebimento")} disabled={Boolean(loadingAction)}>
              Preset: pacote avariado
            </button>
            <button type="button" style={buttonGhostStyle} onClick={() => setExceptionReason("item não encontrado no lote")} disabled={Boolean(loadingAction)}>
              Preset: item não encontrado
            </button>
          </div>
        </label>

        <label style={{ ...labelStyle, marginTop: 10 }}>
          Payload close (JSON)
          <textarea value={closePayload} onChange={(e) => setClosePayload(e.target.value)} style={textareaStyle} />
          <div style={presetRowStyle}>
            <button
              type="button"
              style={buttonGhostStyle}
              onClick={() =>
                setClosePayload('{\n  "actual_parcel_count": 24,\n  "carrier_note": "fechamento com entrega total"\n}')
              }
              disabled={Boolean(loadingAction)}
            >
              Preset: DELIVERED
            </button>
            <button
              type="button"
              style={buttonGhostStyle}
              onClick={() =>
                setClosePayload('{\n  "actual_parcel_count": 22,\n  "carrier_note": "fechamento parcial do lote"\n}')
              }
              disabled={Boolean(loadingAction)}
            >
              Preset: PARTIAL
            </button>
            <button
              type="button"
              style={buttonGhostStyle}
              onClick={() =>
                setClosePayload('{\n  "actual_parcel_count": 0,\n  "carrier_note": "falha operacional no fechamento"\n}')
              }
              disabled={Boolean(loadingAction)}
            >
              Preset: FAILED
            </button>
          </div>
        </label>

        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleListItems()} disabled={Boolean(loadingAction)}>
            {loadingAction === "list-items" ? "Listando..." : "GET items"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleCloseManifest()} disabled={Boolean(loadingAction)}>
            {loadingAction === "close-manifest" ? "Fechando..." : "POST close"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleMarkException()} disabled={Boolean(loadingAction)}>
            {loadingAction === "mark-exception" ? "Marcando..." : "POST exception"}
          </OpsActionButton>
        </div>

        <pre style={resultStyle}>{result || "Execute uma acao para visualizar resposta tecnica."}</pre>
      </section>
    </div>
  );
}

function ActionChip({ label, data }) {
  const normalized = String(data?.status || "idle");
  const palette =
    normalized === "success"
      ? { border: "rgba(16,185,129,0.45)", bg: "rgba(16,185,129,0.12)", color: "#6EE7B7", text: "OK" }
      : normalized === "error"
        ? { border: "rgba(239,68,68,0.45)", bg: "rgba(239,68,68,0.12)", color: "#FCA5A5", text: "ERRO" }
        : normalized === "running"
          ? { border: "rgba(59,130,246,0.45)", bg: "rgba(59,130,246,0.12)", color: "#93C5FD", text: "RUN" }
          : { border: "rgba(148,163,184,0.4)", bg: "rgba(148,163,184,0.1)", color: "#CBD5E1", text: "IDLE" };

  return (
    <article
      style={{
        border: `1px solid ${palette.border}`,
        background: palette.bg,
        borderRadius: 10,
        padding: "8px 10px",
        minWidth: 180,
        display: "grid",
        gap: 4,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 6 }}>
        <strong style={{ fontSize: 12 }}>{label}</strong>
        <span style={{ color: palette.color, fontWeight: 800, fontSize: 11 }}>{palette.text}</span>
      </div>
      <small style={{ color: "#94A3B8" }}>{data?.note || "-"}</small>
      <small style={{ color: "#64748B" }}>Última execução: {data?.at || "-"}</small>
    </article>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8", marginTop: 8 };
const playbookStyle = {
  marginTop: 12,
  padding: 12,
  borderRadius: 12,
  background: "rgba(29,78,216,0.12)",
  border: "1px solid rgba(29,78,216,0.35)",
  display: "grid",
  gap: 8,
};
const playbookListStyle = { margin: 0, paddingLeft: 18, display: "grid", gap: 4 };
const quickActionsStyle = { display: "flex", gap: 8, flexWrap: "wrap" };
const contextHelpStyle = {
  marginTop: 10,
  padding: 10,
  borderRadius: 10,
  background: "rgba(255,255,255,0.05)",
  border: "1px solid rgba(255,255,255,0.10)",
  display: "grid",
  gap: 4,
  fontSize: 13,
};
const chipsRowStyle = { marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" };
const gridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const textareaStyle = { minHeight: 120, padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0", fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace" };
const presetRowStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 6 };
const actionsStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 };
const buttonGhostStyle = { padding: "6px 10px", borderRadius: 999, border: "1px solid #334155", background: "#0B1220", color: "#CBD5E1", fontWeight: 600, cursor: "pointer", fontSize: 12 };
const resultStyle = { marginTop: 12, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 12, overflow: "auto", fontSize: 12, whiteSpace: "pre-wrap" };

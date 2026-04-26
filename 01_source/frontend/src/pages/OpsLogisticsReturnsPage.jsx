import React, { useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsActionButton from "../components/OpsActionButton";
import { getSeverityBadgeStyle } from "../components/opsVisualTokens";
import OpsScenarioPresets from "../components/OpsScenarioPresets";
import useOpsWindowPreset from "../hooks/useOpsWindowPreset";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const FILTERS_PREF_KEY = "ops_logistics_returns:last_filters";
const AUTO_REFRESH_PREF_KEY = "ops_logistics_returns:auto_refresh_on_preset";
const ACTION_CHIPS_PREF_KEY = "ops_logistics_returns:action_chips";
const OPS_LOGISTICS_RETURNS_WINDOW_PREF_KEY = "ops_logistics_returns:window_hours";
const OPS_LOGISTICS_RETURNS_WINDOW_PRESETS = [1, 6, 24, 24 * 7, 24 * 30];

const STATUS_OPTIONS = ["", "REQUESTED", "APPROVED", "REJECTED", "LABEL_ISSUED", "IN_TRANSIT", "RECEIVED", "CLOSED", "DISPUTED"];
const REQUESTER_OPTIONS = ["", "RECIPIENT", "SENDER", "SYSTEM", "OPS"];

function toLocalInputValue(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  const hh = String(date.getHours()).padStart(2, "0");
  const mm = String(date.getMinutes()).padStart(2, "0");
  return `${y}-${m}-${d}T${hh}:${mm}`;
}

function toIsoOrNull(localDateTimeValue) {
  const raw = String(localDateTimeValue || "").trim();
  if (!raw) return null;
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toISOString();
}

function parseError(payload, fallback = "Nao foi possivel carregar retornos de Logistics.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) {
      return payload.detail.message.trim();
    }
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) {
      return payload.detail.type.trim();
    }
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API OPS de Returns.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao com a API OPS (${endpoint}). Verifique se o backend esta ativo e se o proxy /api/op esta configurado no frontend.`;
  }
  return raw;
}

function loadLastFilters(now) {
  const defaultFrom = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  try {
    const raw = window.localStorage.getItem(FILTERS_PREF_KEY);
    if (!raw) {
      return {
        from: toLocalInputValue(defaultFrom),
        to: toLocalInputValue(now),
        partnerId: "",
        status: "",
        preset: "7d",
        limit: 20,
      };
    }
    const parsed = JSON.parse(raw);
    return {
      from: typeof parsed?.from === "string" && parsed.from.trim() ? parsed.from : toLocalInputValue(defaultFrom),
      to: typeof parsed?.to === "string" && parsed.to.trim() ? parsed.to : toLocalInputValue(now),
      partnerId: typeof parsed?.partnerId === "string" ? parsed.partnerId : "",
      status: typeof parsed?.status === "string" ? parsed.status : "",
      preset: typeof parsed?.preset === "string" && parsed.preset.trim() ? parsed.preset : "7d",
      limit: Number.isFinite(parsed?.limit) ? Math.max(1, Math.min(200, Number(parsed.limit))) : 20,
    };
  } catch (_) {
    return {
      from: toLocalInputValue(defaultFrom),
      to: toLocalInputValue(now),
      partnerId: "",
      status: "",
      preset: "7d",
      limit: 20,
    };
  }
}

function persistLastFilters(filters) {
  try {
    window.localStorage.setItem(FILTERS_PREF_KEY, JSON.stringify(filters));
  } catch (_) {
    // fallback silencioso
  }
}

function resolveSeverityByStatus(status) {
  const normalized = String(status || "").toUpperCase();
  if (normalized === "CLOSED") return "OK";
  if (normalized === "APPROVED" || normalized === "LABEL_ISSUED" || normalized === "IN_TRANSIT") return "WARN";
  if (normalized === "RECEIVED") return "WARN";
  return "HIGH";
}

function loadActionChips() {
  try {
    const raw = window.localStorage.getItem(ACTION_CHIPS_PREF_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (_) {
    return {};
  }
}

function persistActionChips(next) {
  try {
    window.localStorage.setItem(ACTION_CHIPS_PREF_KEY, JSON.stringify(next));
  } catch (_) {
    // fallback silencioso
  }
}

function KpiCard({ label, value }) {
  return (
    <article style={kpiCardStyle}>
      <strong style={{ color: "#BFDBFE", display: "block", fontSize: 26 }}>{value}</strong>
      <small style={{ color: "#94A3B8", display: "block", marginTop: 4 }}>{label}</small>
    </article>
  );
}

export default function OpsLogisticsReturnsPage() {
  const { token } = useAuth();
  const now = new Date();
  const last = loadLastFilters(now);
  const defaultWindowHoursByPreset = {
    "1h": 1,
    "6h": 6,
    "24h": 24,
    "7d": 24 * 7,
    "30d": 24 * 30,
  };
  const defaultWindowHours = defaultWindowHoursByPreset[last.preset] || 24 * 7;
  const { applyPreset: applyWindowHoursPreset } = useOpsWindowPreset({
    storageKey: OPS_LOGISTICS_RETURNS_WINDOW_PREF_KEY,
    defaultValue: defaultWindowHours,
    minValue: 1,
    maxValue: 24 * 30,
    presetValues: OPS_LOGISTICS_RETURNS_WINDOW_PRESETS,
  });

  const [from, setFrom] = useState(last.from);
  const [to, setTo] = useState(last.to);
  const [partnerId, setPartnerId] = useState(last.partnerId);
  const [status, setStatus] = useState(last.status);
  const [requesterType, setRequesterType] = useState("");
  const [returnReasonCode, setReturnReasonCode] = useState("");
  const [originalDeliveryId, setOriginalDeliveryId] = useState("");
  const [limit, setLimit] = useState(last.limit);
  const [offset, setOffset] = useState(0);
  const [preset, setPreset] = useState(last.preset);
  const [selectedReturnId, setSelectedReturnId] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("APPROVED");
  const [statusReason, setStatusReason] = useState("Aprovado por triagem OPS.");
  const [chips, setChips] = useState(() => loadActionChips());
  const [autoRefreshOnPreset, setAutoRefreshOnPreset] = useState(() => {
    try {
      const stored = window.localStorage.getItem(AUTO_REFRESH_PREF_KEY);
      if (stored === "true") return true;
      if (stored === "false") return false;
    } catch (_) {
      // fallback silencioso
    }
    return true;
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [payload, setPayload] = useState(null);
  const [detailPayload, setDetailPayload] = useState(null);
  const [slaPayload, setSlaPayload] = useState(null);
  const [copyStatus, setCopyStatus] = useState("");

  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  function persistSnapshot(next = {}) {
    persistLastFilters({
      from: next.from ?? from,
      to: next.to ?? to,
      partnerId: next.partnerId ?? partnerId,
      status: next.status ?? status,
      preset: next.preset ?? preset,
      limit: next.limit ?? limit,
    });
  }

  function pushChip(actionId, statusId, message) {
    setChips((previous) => {
      const next = {
        ...previous,
        [actionId]: {
          status: statusId,
          message,
          at: new Date().toISOString(),
        },
      };
      persistActionChips(next);
      return next;
    });
  }

  function applyPreset(presetId) {
    const referenceNow = new Date();
    let start = new Date(referenceNow.getTime() - 7 * 24 * 60 * 60 * 1000);
    if (presetId === "month") {
      start = new Date(referenceNow.getFullYear(), referenceNow.getMonth(), 1, 0, 0, 0, 0);
    } else {
      const hoursByPreset = {
        "1h": 1,
        "6h": 6,
        "24h": 24,
        "7d": 24 * 7,
        "30d": 24 * 30,
      };
      const windowHours = hoursByPreset[presetId] || 24 * 7;
      applyWindowHoursPreset(windowHours);
      start = new Date(referenceNow.getTime() - windowHours * 60 * 60 * 1000);
    }
    const nextFrom = toLocalInputValue(start);
    const nextTo = toLocalInputValue(referenceNow);
    setFrom(nextFrom);
    setTo(nextTo);
    setPreset(presetId);
    setOffset(0);
    persistSnapshot({ from: nextFrom, to: nextTo, preset: presetId });
    if (autoRefreshOnPreset) {
      setTimeout(() => {
        void loadReturns({ fromOverride: nextFrom, toOverride: nextTo, offsetOverride: 0 });
      }, 0);
    }
  }

  function handleAutoRefreshToggle(nextValue) {
    setAutoRefreshOnPreset(nextValue);
    try {
      window.localStorage.setItem(AUTO_REFRESH_PREF_KEY, String(nextValue));
    } catch (_) {
      // fallback silencioso
    }
  }

  async function loadReturns({ fromOverride = null, toOverride = null, offsetOverride = null } = {}) {
    if (!token) return;
    setLoading(true);
    setError("");
    pushChip("queue", "loading", "Carregando fila de return-requests...");
    try {
      const params = new URLSearchParams();
      const fromIso = toIsoOrNull(fromOverride || from);
      const toIso = toIsoOrNull(toOverride || to);
      if (fromIso) params.set("from", fromIso);
      if (toIso) params.set("to", toIso);
      const normalizedPartner = String(partnerId || "").trim();
      const normalizedStatus = String(status || "").trim().toUpperCase();
      const normalizedRequesterType = String(requesterType || "").trim().toUpperCase();
      const normalizedReturnReasonCode = String(returnReasonCode || "").trim().toUpperCase();
      const normalizedOriginalDelivery = String(originalDeliveryId || "").trim();
      if (normalizedPartner) params.set("partner_id", normalizedPartner);
      if (normalizedStatus) params.set("status", normalizedStatus);
      if (normalizedRequesterType) params.set("requester_type", normalizedRequesterType);
      if (normalizedReturnReasonCode) params.set("return_reason_code", normalizedReturnReasonCode);
      if (normalizedOriginalDelivery) params.set("original_delivery_id", normalizedOriginalDelivery);
      params.set("limit", String(limit));
      params.set("offset", String(offsetOverride ?? offset));

      persistSnapshot({
        from: fromOverride || from,
        to: toOverride || to,
      });

      const endpoint = `${ORDER_PICKUP_BASE}/logistics/return-requests?${params.toString()}`;
      const response = await fetch(endpoint, {
        method: "GET",
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseError(data));
      }
      setPayload(data || null);
      if (offsetOverride !== null && offsetOverride !== undefined) setOffset(offsetOverride);
      pushChip("queue", "ok", `Fila atualizada com ${Number(data?.items?.length || 0)} itens.`);
    } catch (err) {
      const endpoint = `${ORDER_PICKUP_BASE}/logistics/return-requests`;
      setError(normalizeNetworkError(err, endpoint));
      setPayload(null);
      pushChip("queue", "error", `Erro ao atualizar fila: ${normalizeNetworkError(err, endpoint)}`);
    } finally {
      setLoading(false);
    }
  }

  async function loadReturnDetail() {
    if (!token || !selectedReturnId.trim()) return;
    pushChip("detail", "loading", "Carregando detalhe da solicitação...");
    try {
      const endpoint = `${ORDER_PICKUP_BASE}/logistics/return-requests/${encodeURIComponent(selectedReturnId.trim())}`;
      const response = await fetch(endpoint, { method: "GET", headers: { Accept: "application/json", ...authHeaders } });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data, "Falha ao carregar detalhe da devolução."));
      setDetailPayload(data || null);
      pushChip("detail", "ok", `Detalhe carregado (${String(data?.status || "sem status")}).`);
    } catch (err) {
      setDetailPayload(null);
      pushChip("detail", "error", String(err?.message || err || "Erro no detalhe."));
    }
  }

  async function patchSelectedStatus() {
    if (!token || !selectedReturnId.trim() || !selectedStatus.trim()) return;
    pushChip("statusPatch", "loading", `Atualizando status para ${selectedStatus}...`);
    try {
      const endpoint = `${ORDER_PICKUP_BASE}/logistics/return-requests/${encodeURIComponent(selectedReturnId.trim())}/status`;
      const response = await fetch(endpoint, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Accept: "application/json", ...authHeaders },
        body: JSON.stringify({ status: selectedStatus, close_reason: String(statusReason || "").trim() || undefined }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data, "Falha ao atualizar status."));
      setDetailPayload(data || null);
      pushChip("statusPatch", "ok", `Status atualizado: ${String(data?.status || selectedStatus)}.`);
      await loadReturns({ offsetOverride: offset });
    } catch (err) {
      pushChip("statusPatch", "error", String(err?.message || err || "Erro no patch de status."));
    }
  }

  async function issueSelectedLabel() {
    if (!token || !selectedReturnId.trim()) return;
    pushChip("issueLabel", "loading", "Emitindo label de logística reversa...");
    try {
      const endpoint = `${ORDER_PICKUP_BASE}/logistics/return-requests/${encodeURIComponent(selectedReturnId.trim())}/labels`;
      const response = await fetch(endpoint, { method: "POST", headers: { Accept: "application/json", ...authHeaders } });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data, "Falha ao emitir label."));
      pushChip("issueLabel", "ok", `Label emitida: ${String(data?.label_id || data?.id || "ok")}.`);
      await loadReturnDetail();
      await loadReturns({ offsetOverride: offset });
    } catch (err) {
      pushChip("issueLabel", "error", String(err?.message || err || "Erro ao emitir label."));
    }
  }

  async function loadSlaBreaches() {
    if (!token) return;
    pushChip("sla", "loading", "Consultando SLA breaches...");
    try {
      const params = new URLSearchParams();
      if (selectedReturnId.trim()) params.set("return_request_id", selectedReturnId.trim());
      params.set("limit", "30");
      params.set("offset", "0");
      const endpoint = `${ORDER_PICKUP_BASE}/logistics/sla-breaches?${params.toString()}`;
      const response = await fetch(endpoint, { method: "GET", headers: { Accept: "application/json", ...authHeaders } });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data, "Falha ao consultar SLA breaches."));
      setSlaPayload(data || null);
      pushChip("sla", "ok", `${Number(data?.items?.length || 0)} breach(es) retornados.`);
    } catch (err) {
      setSlaPayload(null);
      pushChip("sla", "error", String(err?.message || err || "Erro ao consultar SLA."));
    }
  }

  async function copyEvidence() {
    const lines = [
      `OPS Returns D2 - ${new Date().toISOString()}`,
      `Filtro status=${status || "ALL"} requester_type=${requesterType || "ALL"} reason=${returnReasonCode || "ALL"}`,
      `Fila: total=${total} pagina=${items.length} offset=${offset} limit=${limit}`,
      `Return selecionado: ${selectedReturnId || "-"}`,
      `queue=${chips.queue?.status || "-"} detail=${chips.detail?.status || "-"} patch=${chips.statusPatch?.status || "-"} label=${chips.issueLabel?.status || "-"} sla=${chips.sla?.status || "-"}`,
    ];
    try {
      await navigator.clipboard.writeText(lines.join("\n"));
      setCopyStatus("Evidência copiada para a área de transferência.");
      window.setTimeout(() => setCopyStatus(""), 2400);
    } catch (_) {
      setCopyStatus("Falha ao copiar automaticamente. Copie manualmente do painel.");
    }
  }

  function applyScenarioPreset(kind) {
    if (kind === "green") {
      setStatus("REQUESTED");
      setRequesterType("RECIPIENT");
      setReturnReasonCode("");
      setSelectedStatus("APPROVED");
      setStatusReason("Aprovado por triagem OPS.");
      return;
    }
    if (kind === "amber") {
      setStatus("APPROVED");
      setRequesterType("OPS");
      setReturnReasonCode("DAMAGED_ITEM");
      setSelectedStatus("LABEL_ISSUED");
      setStatusReason("Label emitida para fluxo reverso.");
      return;
    }
    setStatus("DISPUTED");
    setRequesterType("OPS");
    setReturnReasonCode("");
    setSelectedStatus("REJECTED");
    setStatusReason("Rejeitado por inconsistência de evidências.");
  }

  const items = Array.isArray(payload?.items) ? payload.items : [];
  const total = Number(payload?.total || 0);
  const countByStatus = items.reduce((acc, item) => {
    const key = String(item?.status || "UNKNOWN").toUpperCase();
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>OPS - Logistics Returns</h1>
        <p style={mutedStyle}>
          Visão operacional de devoluções com filtros, presets e persistência para continuidade de contexto.
        </p>

        <div style={filtersGridStyle}>
          <label style={labelStyle}>
            From
            <input
              type="datetime-local"
              value={from}
              onChange={(e) => {
                const next = e.target.value;
                setFrom(next);
                persistSnapshot({ from: next });
              }}
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            To
            <input
              type="datetime-local"
              value={to}
              onChange={(e) => {
                const next = e.target.value;
                setTo(next);
                persistSnapshot({ to: next });
              }}
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Partner ID (opcional)
            <input
              value={partnerId}
              onChange={(e) => {
                const next = e.target.value;
                setPartnerId(next);
                persistSnapshot({ partnerId: next });
              }}
              placeholder="ex.: ptn_123"
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Status
            <select
              value={status}
              onChange={(e) => {
                const next = e.target.value;
                setStatus(next);
                persistSnapshot({ status: next });
              }}
              style={inputStyle}
            >
              {STATUS_OPTIONS.map((item) => (
                <option key={item || "ALL"} value={item}>
                  {item || "Todos"}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Requester type
            <select value={requesterType} onChange={(e) => setRequesterType(e.target.value)} style={inputStyle}>
              {REQUESTER_OPTIONS.map((item) => (
                <option key={item || "ALL_REQ"} value={item}>
                  {item || "Todos"}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Return reason code
            <input value={returnReasonCode} onChange={(e) => setReturnReasonCode(e.target.value)} style={inputStyle} placeholder="ex.: DAMAGED_ITEM" />
          </label>
          <label style={labelStyle}>
            Original delivery ID
            <input value={originalDeliveryId} onChange={(e) => setOriginalDeliveryId(e.target.value)} style={inputStyle} placeholder="dlv_..." />
          </label>
          <label style={labelStyle}>
            Limit
            <input
              type="number"
              min={1}
              max={200}
              value={limit}
              onChange={(e) => {
                const next = Math.max(1, Math.min(200, Number(e.target.value || 20)));
                setLimit(next);
                persistSnapshot({ limit: next });
              }}
              style={inputStyle}
            />
          </label>
        </div>

        <div style={presetSectionStyle}>
          <div style={presetHeadRowStyle}>
            <span style={presetLabelStyle}>Presets globais</span>
            <label style={toggleLabelStyle}>
              <input
                type="checkbox"
                checked={autoRefreshOnPreset}
                onChange={(e) => handleAutoRefreshToggle(e.target.checked)}
              />
              Auto refresh on preset click
            </label>
          </div>
          <div style={presetWrapStyle}>
            {[
              { id: "1h", label: "1h" },
              { id: "6h", label: "6h" },
              { id: "24h", label: "24h" },
              { id: "7d", label: "7d" },
              { id: "30d", label: "30d" },
              { id: "month", label: "Mes Atual" },
            ].map((item) => (
              <button key={item.id} type="button" onClick={() => applyPreset(item.id)} style={presetButtonStyle(preset === item.id)}>
                {item.label}
              </button>
            ))}
          </div>
          <OpsScenarioPresets
            style={presetWrapStyle}
            disabled={loading}
            items={[
              { id: "green", tone: "success", label: "Preset verde: triagem saudável", onClick: () => applyScenarioPreset("green") },
              { id: "amber", tone: "warn", label: "Preset âmbar: emitir label", onClick: () => applyScenarioPreset("amber") },
              { id: "red", tone: "error", label: "Preset vermelho: disputa/rejeição", onClick: () => applyScenarioPreset("red") },
            ]}
          />
        </div>

        <div style={actionsRowStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void loadReturns({ offsetOverride: 0 })} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar Returns"}
          </OpsActionButton>
          <OpsActionButton
            type="button"
            onClick={() => void loadReturns({ offsetOverride: Math.max(0, offset - limit) })}
            variant="secondary"
            disabled={loading || offset <= 0}
          >
            Página anterior
          </OpsActionButton>
          <OpsActionButton
            type="button"
            onClick={() => void loadReturns({ offsetOverride: offset + limit })}
            variant="secondary"
            disabled={loading || offset + limit >= total}
          >
            Próxima página
          </OpsActionButton>
          <span style={mutedStyleSmall}>offset={offset} total={total}</span>
        </div>

        {error ? <pre style={errorStyle}>{error}</pre> : null}

        <div style={kpiGridStyle}>
          <KpiCard label="Total retornos (filtro)" value={total} />
          <KpiCard label="REQUESTED (pagina)" value={countByStatus.REQUESTED || 0} />
          <KpiCard label="IN_TRANSIT (pagina)" value={countByStatus.IN_TRANSIT || 0} />
          <KpiCard label="CLOSED (pagina)" value={countByStatus.CLOSED || 0} />
        </div>

        {!payload ? (
          <p style={mutedStyle}>Clique em "Atualizar Returns" para carregar os dados.</p>
        ) : !items.length ? (
          <p style={mutedStyle}>Nenhum retorno encontrado para os filtros atuais.</p>
        ) : (
          <div style={tableWrapStyle}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Return ID</th>
                  <th style={thStyle}>Delivery ID</th>
                  <th style={thStyle}>Requester</th>
                  <th style={thStyle}>Reason</th>
                  <th style={thStyle}>Status</th>
                  <th style={thStyle}>Legs</th>
                  <th style={thStyle}>Updated at</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => {
                  const rowStatus = String(row?.status || "").toUpperCase();
                  const rowId = String(row?.id || "");
                  const isSelected = rowId && rowId === selectedReturnId;
                  return (
                    <tr
                      key={row.id}
                      style={{
                        background: isSelected ? "rgba(59,130,246,0.15)" : "transparent",
                      }}
                    >
                      <td style={tdStyle}>
                        <button
                          type="button"
                          onClick={() => setSelectedReturnId(rowId)}
                          style={{
                            border: "1px solid rgba(148,163,184,0.55)",
                            borderRadius: 8,
                            background: isSelected ? "rgba(59,130,246,0.35)" : "rgba(148,163,184,0.12)",
                            color: "#E2E8F0",
                            padding: "4px 8px",
                            cursor: "pointer",
                            fontWeight: 600,
                          }}
                          aria-label={`Selecionar return ${rowId}`}
                        >
                          {row.id}
                        </button>
                      </td>
                      <td style={tdStyle}>{row.original_delivery_id}</td>
                      <td style={tdStyle}>{row.requester_type}</td>
                      <td style={tdStyle}>{row.return_reason_code}</td>
                      <td style={tdStyle}>
                        <span style={getSeverityBadgeStyle(resolveSeverityByStatus(rowStatus))}>{rowStatus || "-"}</span>
                      </td>
                      <td style={tdStyle}>{Array.isArray(row?.legs) ? row.legs.length : 0}</td>
                      <td style={tdStyle}>{row.updated_at}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        <div style={quickActionsGridStyle}>
          <article style={quickCardStyle}>
            <strong style={{ color: "#BFDBFE" }}>Guia rápido D2</strong>
            <ul style={{ margin: "8px 0 0 16px", color: "#CBD5E1", fontSize: 12, display: "grid", gap: 4 }}>
              <li>Use filtros para montar fila por status, requester e reason.</li>
              <li>Use o botao no Return ID para selecionar `return_request_id` automaticamente.</li>
              <li>Aplique `PATCH status` e depois `Emitir label` para avançar fluxo.</li>
              <li>Valide SLA com filtro pelo retorno selecionado.</li>
            </ul>
          </article>
          <article style={quickCardStyle}>
            <strong style={{ color: "#BFDBFE" }}>Quick actions</strong>
            <div style={{ ...filtersGridStyle, marginTop: 8 }}>
              <label style={labelStyle}>
                Return Request ID
                <input value={selectedReturnId} onChange={(e) => setSelectedReturnId(e.target.value)} style={inputStyle} placeholder="rr_..." />
              </label>
              <label style={labelStyle}>
                Patch status
                <select value={selectedStatus} onChange={(e) => setSelectedStatus(e.target.value)} style={inputStyle}>
                  {STATUS_OPTIONS.filter(Boolean).map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              </label>
              <label style={labelStyle}>
                Close reason / observação
                <input value={statusReason} onChange={(e) => setStatusReason(e.target.value)} style={inputStyle} />
              </label>
            </div>
            <div style={actionsRowStyle}>
              <OpsActionButton type="button" variant="secondary" onClick={() => void loadReturnDetail()}>GET detalhe</OpsActionButton>
              <OpsActionButton type="button" variant="secondary" onClick={() => void patchSelectedStatus()}>PATCH status</OpsActionButton>
              <OpsActionButton type="button" variant="secondary" onClick={() => void issueSelectedLabel()}>Emitir label</OpsActionButton>
              <OpsActionButton type="button" variant="secondary" onClick={() => void loadSlaBreaches()}>GET SLA breaches</OpsActionButton>
              <OpsActionButton type="button" variant="copy" onClick={() => void copyEvidence()}>Copiar evidência</OpsActionButton>
            </div>
            {copyStatus ? <div style={copyStatusStyle}>{copyStatus}</div> : null}
          </article>
        </div>
        <div style={chipsWrapStyle}>
          {[
            ["queue", "Fila"],
            ["detail", "Detalhe"],
            ["statusPatch", "PATCH status"],
            ["issueLabel", "Emitir label"],
            ["sla", "SLA"],
          ].map(([key, label]) => (
            <span key={key} style={chipStyle(chips[key]?.status)}>{label}: {chips[key]?.message || "sem execução"}</span>
          ))}
        </div>
        {detailPayload ? <pre style={jsonStyle}>{JSON.stringify(detailPayload, null, 2)}</pre> : null}
        {slaPayload ? <pre style={jsonStyle}>{JSON.stringify(slaPayload, null, 2)}</pre> : null}
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8", marginTop: 8 };
const mutedStyleSmall = { color: "#94A3B8", fontSize: 12 };
const filtersGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: 10 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const actionsRowStyle = { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginTop: 12 };
const errorStyle = { marginTop: 12, background: "rgba(220, 38, 38, 0.12)", color: "#FCA5A5", border: "1px solid rgba(220, 38, 38, 0.45)", borderRadius: 10, padding: 10 };
const presetSectionStyle = { marginTop: 12, background: "#0B1220", border: "1px solid #1E293B", borderRadius: 10, padding: 10 };
const presetHeadRowStyle = { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, flexWrap: "wrap" };
const presetWrapStyle = { display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8, marginTop: 8 };
const presetLabelStyle = { color: "#94A3B8", fontSize: 12 };
const toggleLabelStyle = { color: "#CBD5E1", fontSize: 12, display: "flex", alignItems: "center", gap: 6 };
const presetButtonStyle = (active) => ({
  padding: "6px 10px",
  borderRadius: 999,
  border: active ? "1px solid #1D4ED8" : "1px solid #334155",
  background: active ? "rgba(29,78,216,0.22)" : "#0B1220",
  color: active ? "#BFDBFE" : "#CBD5E1",
  fontWeight: 700,
  cursor: "pointer",
});
const kpiGridStyle = { marginTop: 16, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10 };
const kpiCardStyle = { background: "#0B1220", border: "1px solid #334155", borderRadius: 12, padding: 12 };
const tableWrapStyle = { marginTop: 16, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 900 };
const thStyle = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const tdStyle = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B" };
const quickActionsGridStyle = { marginTop: 16, display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))" };
const quickCardStyle = { background: "#0B1220", border: "1px solid #334155", borderRadius: 12, padding: 12 };
const chipsWrapStyle = { marginTop: 14, display: "grid", gap: 8 };
const chipStyle = (state) => ({
  display: "inline-flex",
  borderRadius: 999,
  padding: "6px 10px",
  fontSize: 12,
  fontWeight: 700,
  border: state === "ok" ? "1px solid rgba(34,197,94,0.55)" : state === "error" ? "1px solid rgba(239,68,68,0.55)" : "1px solid rgba(148,163,184,0.45)",
  background: state === "ok" ? "rgba(34,197,94,0.15)" : state === "error" ? "rgba(239,68,68,0.15)" : "rgba(30,41,59,0.45)",
  color: state === "ok" ? "#86EFAC" : state === "error" ? "#FCA5A5" : "#CBD5E1",
});
const jsonStyle = { marginTop: 12, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 12, overflow: "auto", fontSize: 12 };
const copyStatusStyle = { marginTop: 8, fontSize: 12, color: "#93C5FD" };

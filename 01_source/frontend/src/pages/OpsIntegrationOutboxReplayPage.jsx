import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import useOpsWindowPreset from "../hooks/useOpsWindowPreset";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const FILTERS_PREF_KEY = "ops_integration_outbox_replay:last_filters";
const AUTO_REFRESH_PREF_KEY = "ops_integration_outbox_replay:auto_refresh_on_preset";
const SEVERITY_MODE_PREF_KEY = "ops_integration_outbox_replay:severity_mode";
const OPS_OUTBOX_REPLAY_WINDOW_PREF_KEY = "ops_integration_outbox_replay:window_hours";
const OPS_OUTBOX_REPLAY_WINDOW_PRESETS = [1, 6, 24, 24 * 7, 24 * 30];
const STATUS_OPTIONS = ["", "PENDING", "FAILED", "DEAD_LETTER", "SKIPPED"];
const EVENT_TYPE_OPTIONS = ["", "ORDER_CREATED", "ORDER_PAID", "ORDER_CANCELLED", "ORDER_FULFILLMENT_UPDATE"];

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

function parseError(payload, fallback = "Nao foi possivel executar replay em lote do outbox.") {
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
  if (!raw) return "Falha de comunicacao com a API OPS de Integracao.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao com a API OPS (${endpoint}). Verifique se o backend esta ativo e se o proxy /api/op esta configurado no frontend.`;
  }
  return raw;
}

function persistSnapshot(snapshot) {
  try {
    window.localStorage.setItem(FILTERS_PREF_KEY, JSON.stringify(snapshot));
  } catch (_) {
    // fallback silencioso
  }
}

function loadSnapshot(now) {
  const defaultFrom = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  try {
    const raw = window.localStorage.getItem(FILTERS_PREF_KEY);
    if (!raw) {
      return {
        from: toLocalInputValue(defaultFrom),
        to: toLocalInputValue(now),
        preset: "24h",
        partnerId: "",
        status: "FAILED",
        eventType: "ORDER_PAID",
        limit: 50,
        dryRun: true,
        runAfterReplay: false,
        maxDeliveriesAfterReplay: 25,
      };
    }
    const parsed = JSON.parse(raw);
    return {
      from: typeof parsed?.from === "string" && parsed.from.trim() ? parsed.from : toLocalInputValue(defaultFrom),
      to: typeof parsed?.to === "string" && parsed.to.trim() ? parsed.to : toLocalInputValue(now),
      preset: typeof parsed?.preset === "string" && parsed.preset.trim() ? parsed.preset : "24h",
      partnerId: typeof parsed?.partnerId === "string" ? parsed.partnerId : "",
      status: typeof parsed?.status === "string" ? parsed.status : "FAILED",
      eventType: typeof parsed?.eventType === "string" ? parsed.eventType : "ORDER_PAID",
      limit: Number.isFinite(parsed?.limit) ? Math.max(1, Math.min(500, Number(parsed.limit))) : 50,
      dryRun: parsed?.dryRun !== false,
      runAfterReplay: parsed?.runAfterReplay === true,
      maxDeliveriesAfterReplay: Number.isFinite(parsed?.maxDeliveriesAfterReplay)
        ? Math.max(1, Math.min(100, Number(parsed.maxDeliveriesAfterReplay)))
        : 25,
    };
  } catch (_) {
    return {
      from: toLocalInputValue(defaultFrom),
      to: toLocalInputValue(now),
      preset: "24h",
      partnerId: "",
      status: "FAILED",
      eventType: "ORDER_PAID",
      limit: 50,
      dryRun: true,
      runAfterReplay: false,
      maxDeliveriesAfterReplay: 25,
    };
  }
}

export default function OpsIntegrationOutboxReplayPage() {
  const { token } = useAuth();
  const now = new Date();
  const snapshot = loadSnapshot(now);
  const defaultWindowHoursByPreset = {
    "1h": 1,
    "6h": 6,
    "24h": 24,
    "7d": 24 * 7,
    "30d": 24 * 30,
  };
  const defaultWindowHours = defaultWindowHoursByPreset[snapshot.preset] || 24;
  const { applyPreset: applyWindowHoursPreset } = useOpsWindowPreset({
    storageKey: OPS_OUTBOX_REPLAY_WINDOW_PREF_KEY,
    defaultValue: defaultWindowHours,
    minValue: 1,
    maxValue: 24 * 30,
    presetValues: OPS_OUTBOX_REPLAY_WINDOW_PRESETS,
  });

  const [from, setFrom] = useState(snapshot.from);
  const [to, setTo] = useState(snapshot.to);
  const [preset, setPreset] = useState(snapshot.preset);
  const [partnerId, setPartnerId] = useState(snapshot.partnerId);
  const [status, setStatus] = useState(snapshot.status);
  const [eventType, setEventType] = useState(snapshot.eventType);
  const [limit, setLimit] = useState(snapshot.limit);
  const [dryRun, setDryRun] = useState(snapshot.dryRun);
  const [runAfterReplay, setRunAfterReplay] = useState(snapshot.runAfterReplay);
  const [maxDeliveriesAfterReplay, setMaxDeliveriesAfterReplay] = useState(snapshot.maxDeliveriesAfterReplay);
  const [autoRefreshOnPreset, setAutoRefreshOnPreset] = useState(() => {
    try {
      const stored = window.localStorage.getItem(AUTO_REFRESH_PREF_KEY);
      if (stored === "true") return true;
      if (stored === "false") return false;
    } catch (_) {
      // fallback silencioso
    }
    return false;
  });
  const [severityMode, setSeverityMode] = useState(() => {
    try {
      const stored = String(window.localStorage.getItem(SEVERITY_MODE_PREF_KEY) || "").trim().toLowerCase();
      return stored === "tolerant" ? "tolerant" : "strict";
    } catch (_) {
      return "strict";
    }
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [clientGuardError, setClientGuardError] = useState("");
  const [result, setResult] = useState(null);
  const [lastEvidenceAt, setLastEvidenceAt] = useState("");
  const [lastRequestSnapshot, setLastRequestSnapshot] = useState(null);

  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  function storeCurrent(overrides = {}) {
    persistSnapshot({
      from: overrides.from ?? from,
      to: overrides.to ?? to,
      preset: overrides.preset ?? preset,
      partnerId: overrides.partnerId ?? partnerId,
      status: overrides.status ?? status,
      eventType: overrides.eventType ?? eventType,
      limit: overrides.limit ?? limit,
      dryRun: overrides.dryRun ?? dryRun,
      runAfterReplay: overrides.runAfterReplay ?? runAfterReplay,
      maxDeliveriesAfterReplay: overrides.maxDeliveriesAfterReplay ?? maxDeliveriesAfterReplay,
    });
  }

  function applyPreset(presetId) {
    const referenceNow = new Date();
    const hoursByPreset = {
      "1h": 1,
      "6h": 6,
      "24h": 24,
      "7d": 24 * 7,
      "30d": 24 * 30,
    };
    const windowHours = hoursByPreset[presetId] || 24;
    applyWindowHoursPreset(windowHours);
    const start = new Date(referenceNow.getTime() - windowHours * 60 * 60 * 1000);
    const nextFrom = toLocalInputValue(start);
    const nextTo = toLocalInputValue(referenceNow);
    setFrom(nextFrom);
    setTo(nextTo);
    setPreset(presetId);
    storeCurrent({ from: nextFrom, to: nextTo, preset: presetId });
    if (autoRefreshOnPreset) {
      setTimeout(() => {
        void executeReplay({ fromOverride: nextFrom, toOverride: nextTo });
      }, 0);
    }
  }

  function validateGuardRails({ nextDryRun, nextRunAfterReplay, nextLimit, nextMaxDeliveriesAfterReplay }) {
    if (nextRunAfterReplay && nextDryRun) {
      return "Guard rail: run_after_replay=true exige dry_run=false.";
    }
    if (nextRunAfterReplay && Number(nextLimit) > 100) {
      return "Guard rail: com run_after_replay=true, o limit deve ser <= 100.";
    }
    if (!nextRunAfterReplay && Number(nextMaxDeliveriesAfterReplay) > 0) {
      return "Guard rail: max_deliveries_after_replay so pode ser usado quando run_after_replay=true.";
    }
    if (nextRunAfterReplay && Number(nextMaxDeliveriesAfterReplay) > 100) {
      return "Guard rail: max_deliveries_after_replay deve ser <= 100.";
    }
    return "";
  }

  async function executeReplay({ fromOverride = null, toOverride = null } = {}) {
    if (!token) return;
    setLoading(true);
    setError("");
    setClientGuardError("");
    try {
      const localFrom = fromOverride || from;
      const localTo = toOverride || to;
      const fromIso = toIsoOrNull(localFrom);
      const toIso = toIsoOrNull(localTo);
      const guardError = validateGuardRails({
        nextDryRun: dryRun,
        nextRunAfterReplay: runAfterReplay,
        nextLimit: limit,
        nextMaxDeliveriesAfterReplay: runAfterReplay ? maxDeliveriesAfterReplay : 0,
      });
      if (guardError) {
        setClientGuardError(guardError);
        setResult(null);
        return;
      }

      const params = new URLSearchParams();
      params.set("dry_run", String(dryRun));
      params.set("run_after_replay", String(runAfterReplay));
      params.set("limit", String(limit));
      if (runAfterReplay) params.set("max_deliveries_after_replay", String(maxDeliveriesAfterReplay));
      if (fromIso) params.set("period_from", fromIso);
      if (toIso) params.set("period_to", toIso);
      if (String(partnerId || "").trim()) params.set("partner_id", String(partnerId).trim());
      if (String(status || "").trim()) params.set("status", String(status).trim().toUpperCase());
      if (String(eventType || "").trim()) params.set("event_type", String(eventType).trim().toUpperCase());

      const endpoint = `${ORDER_PICKUP_BASE}/ops/integration/order-events-outbox/replay-batch?${params.toString()}`;
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));

      setResult(data || null);
      setLastEvidenceAt(new Date().toLocaleString("pt-BR"));
      setLastRequestSnapshot({
        dry_run: dryRun,
        run_after_replay: runAfterReplay,
        max_deliveries_after_replay: runAfterReplay ? maxDeliveriesAfterReplay : null,
        limit,
        period_from: fromIso,
        period_to: toIso,
        partner_id: String(partnerId || "").trim() || null,
        status: String(status || "").trim() || null,
        event_type: String(eventType || "").trim() || null,
      });
      storeCurrent({ from: localFrom, to: localTo });
    } catch (err) {
      const endpoint = `${ORDER_PICKUP_BASE}/ops/integration/order-events-outbox/replay-batch`;
      setError(normalizeNetworkError(err, endpoint));
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  const resultItems = Array.isArray(result?.items) ? result.items : [];
  const auditShortcutTo = useMemo(() => {
    const params = new URLSearchParams();
    params.set("action", "I1_OUTBOX_MANUAL_REPLAY_BATCH");
    params.set("limit", "50");
    return `/ops/audit?${params.toString()}`;
  }, []);
  const contextualAuditShortcutTo = useMemo(() => {
    if (!result) return "";
    const params = new URLSearchParams();
    params.set("action", "I1_OUTBOX_MANUAL_REPLAY_BATCH");
    params.set("limit", "50");
    params.set("severity_mode", severityMode);
    if (severityMode === "strict") params.set("skipped_policy", "error");
    else params.set("skipped_policy", "warn");
    const hasError =
      String(result?.ok) !== "true" ||
      (severityMode === "strict" && Number(result?.skipped_count || 0) > 0) ||
      Number(result?.worker_run?.failed || 0) > 0 ||
      Number(result?.worker_run?.dead_letter || 0) > 0;
    params.set("result", hasError ? "ERROR" : "SUCCESS");
    return `/ops/audit?${params.toString()}`;
  }, [result, severityMode]);
  const contextualAuditLabel = useMemo(() => {
    if (!result) return "";
    const hasError =
      String(result?.ok) !== "true" ||
      (severityMode === "strict" && Number(result?.skipped_count || 0) > 0) ||
      Number(result?.worker_run?.failed || 0) > 0 ||
      Number(result?.worker_run?.dead_letter || 0) > 0;
    return hasError
      ? `Ir para auditoria contextual (result=ERROR · modo=${severityMode === "strict" ? "estrito" : "tolerante"})`
      : `Ir para auditoria contextual (result=SUCCESS · modo=${severityMode === "strict" ? "estrito" : "tolerante"})`;
  }, [result, severityMode]);

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS - Integration Outbox Replay" />
        <p style={mutedStyle}>
          Painel operacional para replay controlado do outbox com guard rails explícitos, execução opcional do worker e evidência imediata.
        </p>
        <div style={shortcutRowStyle}>
          <Link to={auditShortcutTo} style={shortcutLinkStyle}>
            Ir para auditoria filtrada (I1_OUTBOX_MANUAL_REPLAY_BATCH)
          </Link>
        </div>

        <div style={guardRailBoxStyle}>
          <strong style={{ color: "#F8FAFC" }}>Guard rails (obrigatórios)</strong>
          <ul style={guardRailListStyle}>
            <li>`run_after_replay=true` exige `dry_run=false`</li>
            <li>`run_after_replay=true` exige `limit &lt;= 100`</li>
            <li>`max_deliveries_after_replay` exige `run_after_replay=true` e `&lt;= 100`</li>
          </ul>
        </div>

        <div style={filtersGridStyle}>
          <label style={labelStyle}>
            From
            <input
              type="datetime-local"
              value={from}
              onChange={(e) => {
                setFrom(e.target.value);
                storeCurrent({ from: e.target.value });
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
                setTo(e.target.value);
                storeCurrent({ to: e.target.value });
              }}
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Partner ID (opcional)
            <input
              value={partnerId}
              onChange={(e) => {
                setPartnerId(e.target.value);
                storeCurrent({ partnerId: e.target.value });
              }}
              placeholder="ptn_..."
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Status
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                storeCurrent({ status: e.target.value });
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
            Event type
            <select
              value={eventType}
              onChange={(e) => {
                setEventType(e.target.value);
                storeCurrent({ eventType: e.target.value });
              }}
              style={inputStyle}
            >
              {EVENT_TYPE_OPTIONS.map((item) => (
                <option key={item || "ALL"} value={item}>
                  {item || "Todos"}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Limit
            <input
              type="number"
              min={1}
              max={500}
              value={limit}
              onChange={(e) => {
                const next = Math.max(1, Math.min(500, Number(e.target.value || 50)));
                setLimit(next);
                storeCurrent({ limit: next });
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
                onChange={(e) => {
                  setAutoRefreshOnPreset(e.target.checked);
                  try {
                    window.localStorage.setItem(AUTO_REFRESH_PREF_KEY, String(e.target.checked));
                  } catch (_) {
                    // fallback silencioso
                  }
                }}
              />
              Auto executar no clique do preset
            </label>
          </div>
          <div style={presetWrapStyle}>
            {[
              { id: "1h", label: "1h" },
              { id: "6h", label: "6h" },
              { id: "24h", label: "24h" },
              { id: "7d", label: "7d" },
              { id: "30d", label: "30d" },
            ].map((item) => (
              <button key={item.id} type="button" onClick={() => applyPreset(item.id)} style={presetButtonStyle(preset === item.id)}>
                {item.label}
              </button>
            ))}
          </div>
        </div>

        <div style={guardControlsStyle}>
          <label style={labelStyle}>
            Severidade NOC (skipped)
            <select
              value={severityMode}
              onChange={(e) => {
                const next = e.target.value === "tolerant" ? "tolerant" : "strict";
                setSeverityMode(next);
                try {
                  window.localStorage.setItem(SEVERITY_MODE_PREF_KEY, next);
                } catch (_) {
                  // fallback silencioso
                }
              }}
              style={inputStyle}
            >
              <option value="strict">Estrito (skipped = erro)</option>
              <option value="tolerant">Tolerante (skipped = warning)</option>
            </select>
          </label>
          <label style={toggleLabelStyle}>
            <input
              type="checkbox"
              checked={dryRun}
              onChange={(e) => {
                const next = e.target.checked;
                setDryRun(next);
                storeCurrent({ dryRun: next });
              }}
            />
            Dry run (recomendado para inspeção inicial)
          </label>
          <label style={toggleLabelStyle}>
            <input
              type="checkbox"
              checked={runAfterReplay}
              onChange={(e) => {
                const next = e.target.checked;
                setRunAfterReplay(next);
                storeCurrent({ runAfterReplay: next });
              }}
            />
            Executar worker apos replay
          </label>
          <label style={labelStyle}>
            max_deliveries_after_replay
            <input
              type="number"
              min={1}
              max={100}
              disabled={!runAfterReplay}
              value={maxDeliveriesAfterReplay}
              onChange={(e) => {
                const next = Math.max(1, Math.min(100, Number(e.target.value || 25)));
                setMaxDeliveriesAfterReplay(next);
                storeCurrent({ maxDeliveriesAfterReplay: next });
              }}
              style={{ ...inputStyle, opacity: runAfterReplay ? 1 : 0.6 }}
            />
          </label>
        </div>

        <div style={actionsRowStyle}>
          <button type="button" style={buttonStyle} onClick={() => void executeReplay()} disabled={loading}>
            {loading ? "Executando..." : "Executar replay em lote"}
          </button>
        </div>

        {clientGuardError ? <pre style={warnStyle}>{clientGuardError}</pre> : null}
        {error ? <pre style={errorStyle}>{error}</pre> : null}

        {result ? (
          <>
            <div style={kpiGridStyle}>
              <Kpi label="Selecionados" value={result?.selected_count ?? 0} />
              <Kpi label="Replayed" value={result?.replayed_count ?? 0} />
              <Kpi label="Skipped" value={result?.skipped_count ?? 0} />
              <Kpi label="Total candidates" value={result?.total_candidates ?? 0} />
            </div>

            <div style={evidenceCardStyle}>
              <h3 style={{ marginTop: 0 }}>Evidencia operacional</h3>
              <p style={mutedStyleSmall}>Ultima execucao: {lastEvidenceAt || "-"}</p>
              <p style={mutedStyleSmall}>
                Critério atual:{" "}
                <b>{severityMode === "strict" ? "Estrito (skipped como erro)" : "Tolerante (skipped como warning)"}</b>
              </p>
              {contextualAuditShortcutTo ? (
                <div style={evidenceShortcutRowStyle}>
                  <Link to={contextualAuditShortcutTo} style={shortcutLinkStyle}>
                    {contextualAuditLabel}
                  </Link>
                </div>
              ) : null}
              <pre style={jsonBlockStyle}>{JSON.stringify({ request: lastRequestSnapshot, response: result }, null, 2)}</pre>
              {result?.worker_run ? (
                <div style={workerRowStyle}>
                  <span style={workerBadgeStyle}>worker scanned: {result.worker_run.scanned}</span>
                  <span style={workerBadgeStyle}>delivered: {result.worker_run.delivered}</span>
                  <span style={workerBadgeStyle}>failed: {result.worker_run.failed}</span>
                  <span style={workerBadgeStyle}>dead_letter: {result.worker_run.dead_letter}</span>
                  <span style={workerBadgeStyle}>skipped: {result.worker_run.skipped}</span>
                </div>
              ) : null}
            </div>

            {resultItems.length ? (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Outbox ID</th>
                      <th style={thStyle}>Partner</th>
                      <th style={thStyle}>Event</th>
                      <th style={thStyle}>Status final</th>
                      <th style={thStyle}>Attempts</th>
                      <th style={thStyle}>Created at</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resultItems.map((item) => (
                      <tr key={item.id}>
                        <td style={tdStyle}>{item.id}</td>
                        <td style={tdStyle}>{item.partner_id}</td>
                        <td style={tdStyle}>{item.event_type}</td>
                        <td style={tdStyle}>{item.status}</td>
                        <td style={tdStyle}>{item.attempt_count}/{item.max_attempts}</td>
                        <td style={tdStyle}>{item.created_at}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={mutedStyle}>Sem itens retornados para os filtros selecionados.</p>
            )}
          </>
        ) : (
          <p style={mutedStyle}>Configure os filtros e execute para gerar evidência operacional.</p>
        )}
      </section>
    </div>
  );
}

function Kpi({ label, value }) {
  return (
    <div style={kpiCardStyle}>
      <div style={kpiLabelStyle}>{label}</div>
      <div style={kpiValueStyle}>{value}</div>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8", marginTop: 8 };
const mutedStyleSmall = { color: "#94A3B8", margin: 0, fontSize: 12 };
const filtersGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: 10 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const buttonStyle = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const actionsRowStyle = { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginTop: 12 };
const errorStyle = { marginTop: 12, background: "rgba(220, 38, 38, 0.12)", color: "#FCA5A5", border: "1px solid rgba(220, 38, 38, 0.45)", borderRadius: 10, padding: 10 };
const warnStyle = { marginTop: 12, background: "rgba(245, 158, 11, 0.12)", color: "#FDE68A", border: "1px solid rgba(245, 158, 11, 0.45)", borderRadius: 10, padding: 10 };
const kpiGridStyle = { marginTop: 16, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 10 };
const kpiCardStyle = { background: "#0B1220", border: "1px solid #334155", borderRadius: 12, padding: 12 };
const kpiLabelStyle = { fontSize: 12, color: "#94A3B8" };
const kpiValueStyle = { fontSize: 20, fontWeight: 700, color: "#E2E8F0" };
const tableWrapStyle = { marginTop: 16, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 1000 };
const thStyle = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const tdStyle = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B" };
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
const guardRailBoxStyle = {
  marginBottom: 12,
  background: "rgba(15,23,42,0.85)",
  border: "1px solid rgba(96,165,250,0.45)",
  borderRadius: 10,
  padding: 10,
};
const guardRailListStyle = { margin: "8px 0 0", paddingLeft: 18, color: "#BFDBFE", fontSize: 12, lineHeight: 1.5 };
const guardControlsStyle = {
  marginTop: 12,
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
  gap: 10,
  alignItems: "end",
};
const evidenceCardStyle = {
  marginTop: 16,
  background: "#0B1220",
  border: "1px solid #334155",
  borderRadius: 12,
  padding: 12,
};
const jsonBlockStyle = {
  marginTop: 8,
  background: "#020617",
  border: "1px solid #1E293B",
  borderRadius: 10,
  color: "#E2E8F0",
  padding: 10,
  maxHeight: 260,
  overflow: "auto",
  fontSize: 12,
};
const workerRowStyle = { marginTop: 8, display: "flex", flexWrap: "wrap", gap: 8 };
const workerBadgeStyle = {
  border: "1px solid rgba(96,165,250,0.45)",
  background: "rgba(96,165,250,0.16)",
  color: "#BFDBFE",
  borderRadius: 999,
  padding: "4px 10px",
  fontSize: 12,
  fontWeight: 700,
};
const shortcutRowStyle = { display: "flex", justifyContent: "flex-end", marginBottom: 10 };
const evidenceShortcutRowStyle = { display: "flex", justifyContent: "flex-end", marginTop: 8, marginBottom: 8 };
const shortcutLinkStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(96,165,250,0.15)",
  color: "#bfdbfe",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 13,
};

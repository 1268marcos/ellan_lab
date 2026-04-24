import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

function extractErrorMessage(payload, fallback = "Não foi possível carregar trilha de auditoria.") {
  if (!payload) return fallback;
  if (typeof payload.detail === "string" && payload.detail.trim()) {
    return payload.detail.trim();
  }
  if (payload.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) {
      return payload.detail.message.trim();
    }
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) {
      return payload.detail.type.trim();
    }
  }
  if (typeof payload.message === "string" && payload.message.trim()) {
    return payload.message.trim();
  }
  return fallback;
}

function toDateTimeLocalInputValue(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function toIsoOrNull(localDateTimeValue) {
  const raw = String(localDateTimeValue || "").trim();
  if (!raw) return null;
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toISOString();
}

const ACTION_OPTIONS = [
  "",
  "OPS_RECONCILE_ORDER",
  "OPS_RECON_PENDING_LIST",
  "OPS_RECON_PENDING_RUN_ONCE",
  "OPS_AUDIT_LIST",
  "OPS_METRICS_VIEW",
  "OPS_ORDERS_STATUS_AUDIT",
  "OPS_ORDERS_STATUS_AUDIT_RANGE",
  "OPS_ORDERS_STATUS_AUDIT_EXPORT",
];

const RESULT_OPTIONS = ["", "SUCCESS", "ERROR"];
const MAIN_LIMIT_OPTIONS = [20, 50, 100, 200];
const STATUS_LIMIT_OPTIONS = [100, 200, 500, 1000, 2000];

export default function OpsAuditPage() {
  const { token } = useAuth();
  const now = new Date();
  const last24h = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [limit, setLimit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [orderId, setOrderId] = useState("");
  const [action, setAction] = useState("");
  const [result, setResult] = useState("");
  const [auditFrom, setAuditFrom] = useState(toDateTimeLocalInputValue(last24h));
  const [auditTo, setAuditTo] = useState(toDateTimeLocalInputValue(now));
  const [statusLimit, setStatusLimit] = useState(200);
  const [statusOffset, setStatusOffset] = useState(0);
  const [statusHasMore, setStatusHasMore] = useState(false);
  const [opsHasMore, setOpsHasMore] = useState(false);
  const [statusAuditItems, setStatusAuditItems] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState("24h");
  const didInitialLoadRef = useRef(false);

  const authHeaders = useMemo(() => {
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, [token]);
  const storageKey = useMemo(() => {
    const suffix = token ? token.slice(0, 16) : "anonymous";
    return `ops-audit-filters:v1:${suffix}`;
  }, [token]);

  function applyRangePreset(presetId) {
    const referenceNow = new Date();
    let start = new Date(referenceNow.getTime() - 24 * 60 * 60 * 1000);
    if (presetId === "7d") {
      start = new Date(referenceNow.getTime() - 7 * 24 * 60 * 60 * 1000);
    } else if (presetId === "30d") {
      start = new Date(referenceNow.getTime() - 30 * 24 * 60 * 60 * 1000);
    } else if (presetId === "month") {
      start = new Date(referenceNow.getFullYear(), referenceNow.getMonth(), 1, 0, 0, 0, 0);
    }
    setAuditFrom(toDateTimeLocalInputValue(start));
    setAuditTo(toDateTimeLocalInputValue(referenceNow));
    setStatusOffset(0);
    setSelectedPreset(presetId);
  }

  function resetToShiftDefaults() {
    const confirmation = window.confirm(
      "Resetar todos os filtros para o padrão de plantão (24h e offsets zerados)?"
    );
    if (!confirmation) return;

    const referenceNow = new Date();
    const start24h = new Date(referenceNow.getTime() - 24 * 60 * 60 * 1000);

    setOrderId("");
    setAction("");
    setResult("");
    setLimit(20);
    setOffset(0);

    setAuditFrom(toDateTimeLocalInputValue(start24h));
    setAuditTo(toDateTimeLocalInputValue(referenceNow));
    setStatusLimit(200);
    setStatusOffset(0);
    setSelectedPreset("24h");

    const nextAuditFrom = toDateTimeLocalInputValue(start24h);
    const nextAuditTo = toDateTimeLocalInputValue(referenceNow);
    loadAudit(0, {
      orderId: "",
      action: "",
      result: "",
      limit: 20,
      offset: 0,
    });
    loadStatusAudit(0, {
      auditFrom: nextAuditFrom,
      auditTo: nextAuditTo,
      statusLimit: 200,
      statusOffset: 0,
    });
  }

  async function loadAudit(nextOffset = null, overrides = null) {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const effectiveOffset = Math.max(Number(nextOffset ?? overrides?.offset ?? offset ?? 0), 0);
      const effectiveLimit = Math.min(Math.max(Number((overrides?.limit ?? limit) ?? 20), 1), 200);
      const effectiveOrderId = String(overrides?.orderId ?? orderId ?? "").trim();
      const effectiveAction = String(overrides?.action ?? action ?? "").trim();
      const effectiveResult = String(overrides?.result ?? result ?? "").trim();
      const params = new URLSearchParams();
      params.set("limit", String(effectiveLimit));
      params.set("offset", String(effectiveOffset));
      if (effectiveOrderId) params.set("order_id", effectiveOrderId);
      if (effectiveAction) params.set("action", effectiveAction);
      if (effectiveResult) params.set("result", effectiveResult);

      const response = await fetch(`${ORDER_PICKUP_BASE}/dev-admin/ops-audit?${params.toString()}`, {
        method: "GET",
        headers: {
          Accept: "application/json",
          ...authHeaders,
        },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(extractErrorMessage(payload));
      }
      const rows = Array.isArray(payload?.items) ? payload.items : [];
      setItems(rows);
      setTotal(Number(payload?.total || rows.length || 0));
      setOffset(effectiveOffset);
      setOpsHasMore(rows.length >= effectiveLimit);
    } catch (err) {
      setError(String(err?.message || err));
      setItems([]);
      setTotal(0);
      setOpsHasMore(false);
    } finally {
      setLoading(false);
    }
  }

  async function loadStatusAudit(nextOffset = null, overrides = null) {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const fromIso = toIsoOrNull(overrides?.auditFrom ?? auditFrom);
      const toIso = toIsoOrNull(overrides?.auditTo ?? auditTo);
      if (!fromIso || !toIso) {
        throw new Error("Preencha from/to com datas válidas.");
      }

      const effectiveOffset = Math.max(Number(nextOffset ?? overrides?.statusOffset ?? statusOffset ?? 0), 0);
      const effectiveLimit = Math.min(Math.max(Number((overrides?.statusLimit ?? statusLimit) ?? 200), 1), 2000);
      const params = new URLSearchParams();
      params.set("from", fromIso);
      params.set("to", toIso);
      params.set("limit", String(effectiveLimit));
      params.set("offset", String(effectiveOffset));
      const response = await fetch(
        `${ORDER_PICKUP_BASE}/dev-admin/orders-status-audit/range?${params.toString()}`,
        {
          method: "GET",
          headers: {
            Accept: "application/json",
            ...authHeaders,
          },
        }
      );
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(extractErrorMessage(payload, "Não foi possível carregar auditoria de status."));
      }
      setStatusAuditItems(Array.isArray(payload?.items) ? payload.items : []);
      setStatusHasMore(Boolean(payload?.has_more));
      setStatusOffset(effectiveOffset);
    } catch (err) {
      setError(String(err?.message || err));
      setStatusAuditItems([]);
      setStatusHasMore(false);
    } finally {
      setLoading(false);
    }
  }

  async function exportStatusAuditCsv() {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const fromIso = toIsoOrNull(auditFrom);
      const toIso = toIsoOrNull(auditTo);
      if (!fromIso || !toIso) {
        throw new Error("Preencha from/to com datas válidas.");
      }
      const params = new URLSearchParams();
      params.set("from", fromIso);
      params.set("to", toIso);
      params.set("limit", "20000");

      const response = await fetch(
        `${ORDER_PICKUP_BASE}/dev-admin/orders-status-audit/export.csv?${params.toString()}`,
        {
          method: "GET",
          headers: {
            Accept: "text/csv",
            ...authHeaders,
          },
        }
      );
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(extractErrorMessage(payload, "Não foi possível exportar CSV."));
      }

      const blob = await response.blob();
      const objectUrl = window.URL.createObjectURL(blob);
      const downloadLink = document.createElement("a");
      downloadLink.href = objectUrl;
      downloadLink.download = `ops-orders-status-audit-${new Date().toISOString()}.csv`;
      document.body.appendChild(downloadLink);
      downloadLink.click();
      downloadLink.remove();
      window.URL.revokeObjectURL(objectUrl);
    } catch (err) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  function handleMainFiltersKeyDown(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      loadAudit(0);
    }
  }

  function handleStatusFiltersKeyDown(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      loadStatusAudit(0);
    }
  }

  useEffect(() => {
    if (!token) return;
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (typeof parsed.orderId === "string") setOrderId(parsed.orderId);
      if (typeof parsed.action === "string") setAction(parsed.action);
      if (typeof parsed.result === "string") setResult(parsed.result);
      if (Number.isFinite(parsed.limit)) setLimit(Math.min(Math.max(Number(parsed.limit), 1), 200));
      if (Number.isFinite(parsed.offset)) setOffset(Math.max(Number(parsed.offset), 0));
      if (typeof parsed.auditFrom === "string" && parsed.auditFrom.trim()) setAuditFrom(parsed.auditFrom);
      if (typeof parsed.auditTo === "string" && parsed.auditTo.trim()) setAuditTo(parsed.auditTo);
      if (Number.isFinite(parsed.statusLimit)) {
        setStatusLimit(Math.min(Math.max(Number(parsed.statusLimit), 1), 2000));
      }
      if (Number.isFinite(parsed.statusOffset)) setStatusOffset(Math.max(Number(parsed.statusOffset), 0));
      if (typeof parsed.selectedPreset === "string" && parsed.selectedPreset.trim()) {
        setSelectedPreset(parsed.selectedPreset);
      }
    } catch (_err) {
      // Ignore corrupted local storage payloads and keep defaults.
    }
  }, [token, storageKey]);

  useEffect(() => {
    if (!token) return;
    const payload = {
      orderId,
      action,
      result,
      limit,
      offset,
      auditFrom,
      auditTo,
      statusLimit,
      statusOffset,
      selectedPreset,
    };
    try {
      localStorage.setItem(storageKey, JSON.stringify(payload));
    } catch (_err) {
      // Ignore storage quota/access errors in restricted browsers.
    }
  }, [
    token,
    storageKey,
    orderId,
    action,
    result,
    limit,
    offset,
    auditFrom,
    auditTo,
    statusLimit,
    statusOffset,
    selectedPreset,
  ]);

  useEffect(() => {
    if (!token || didInitialLoadRef.current) return;
    didInitialLoadRef.current = true;
    loadAudit(0);
    loadStatusAudit(0);
  }, [token]);

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <Link to="/ops/reconciliation" style={shortcutLinkStyle}>
            Ir para reconciliação
          </Link>
          <Link to="/ops/health" style={shortcutLinkStyle}>
            Ir para saúde operacional
          </Link>
        </div>

        <h1 style={{ marginTop: 0 }}>OPS - Trilha de Auditoria</h1>
        <p style={mutedTextStyle}>
          Consulte ações operacionais por ordem, resultado e tipo de ação.
        </p>

        <div style={filtersGridStyle}>
          <label style={labelStyle}>
            Order ID
            <input
              type="text"
              value={orderId}
              onChange={(event) => setOrderId(event.target.value)}
              onKeyDown={handleMainFiltersKeyDown}
              placeholder="2dd793dd-..."
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Action
            <select
              value={action}
              onChange={(event) => setAction(event.target.value)}
              onKeyDown={handleMainFiltersKeyDown}
              style={inputStyle}
            >
              {ACTION_OPTIONS.map((option) => (
                <option key={option || "all"} value={option}>
                  {option || "Todos"}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Result
            <select
              value={result}
              onChange={(event) => setResult(event.target.value)}
              onKeyDown={handleMainFiltersKeyDown}
              style={inputStyle}
            >
              {RESULT_OPTIONS.map((option) => (
                <option key={option || "all"} value={option}>
                  {option || "Todos"}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Limit
            <select
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value || 20))}
              onKeyDown={handleMainFiltersKeyDown}
              style={inputStyle}
            >
              {MAIN_LIMIT_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Offset
            <input
              type="number"
              min={0}
              value={offset}
              onChange={(event) => setOffset(Number(event.target.value || 0))}
              onKeyDown={handleMainFiltersKeyDown}
              style={inputStyle}
            />
          </label>
        </div>

        <div style={actionsRowStyle}>
          <button type="button" onClick={() => loadAudit(0)} style={buttonStyle} disabled={loading}>
            {loading ? "Consultando..." : "Consultar auditoria"}
          </button>
          <button type="button" onClick={resetToShiftDefaults} style={buttonDangerStyle} disabled={loading}>
            Resetar filtros
          </button>
          <button
            type="button"
            onClick={() => loadAudit(0)}
            style={buttonStyle}
            disabled={loading || offset === 0}
          >
            Primeira página
          </button>
          <button
            type="button"
            onClick={() => loadAudit(Math.max(offset - limit, 0))}
            style={buttonStyle}
            disabled={loading || offset === 0}
          >
            Página anterior
          </button>
          <button
            type="button"
            onClick={() => loadAudit(offset + limit)}
            style={buttonStyle}
            disabled={loading || !opsHasMore}
          >
            Próxima página
          </button>
          <span style={{ color: "rgba(245,247,250,0.8)" }}>Total retornado: {total}</span>
          <span style={{ color: "rgba(245,247,250,0.8)" }}>
            Offset atual: {offset} | Itens nesta página: {items.length}
          </span>
        </div>

        <section style={subCardStyle}>
          <h3 style={{ marginTop: 0, marginBottom: 8 }}>Auditoria histórica de status</h3>
          <p style={subtleTextStyle}>
            Investigue períodos longos com paginação por intervalo e exportação CSV.
          </p>

          <div style={filtersGridStyle}>
            <label style={labelStyle}>
              From
              <input
                type="datetime-local"
                value={auditFrom}
                onChange={(event) => setAuditFrom(event.target.value)}
                onKeyDown={handleStatusFiltersKeyDown}
                style={inputStyle}
              />
            </label>
            <label style={labelStyle}>
              To
              <input
                type="datetime-local"
                value={auditTo}
                onChange={(event) => setAuditTo(event.target.value)}
                onKeyDown={handleStatusFiltersKeyDown}
                style={inputStyle}
              />
            </label>
            <label style={labelStyle}>
              Limit
              <select
                value={statusLimit}
                onChange={(event) => setStatusLimit(Number(event.target.value || 200))}
                onKeyDown={handleStatusFiltersKeyDown}
                style={inputStyle}
              >
                {STATUS_LIMIT_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <label style={labelStyle}>
              Offset
              <input
                type="number"
                min={0}
                value={statusOffset}
                onChange={(event) => setStatusOffset(Number(event.target.value || 0))}
                onKeyDown={handleStatusFiltersKeyDown}
                style={inputStyle}
              />
            </label>
          </div>

          <div style={presetRowStyle}>
            <span style={presetLabelStyle}>Presets globais:</span>
            <button
              type="button"
              onClick={() => applyRangePreset("24h")}
              style={buttonPresetStyle(selectedPreset === "24h")}
              disabled={loading}
            >
              24h
            </button>
            <button
              type="button"
              onClick={() => applyRangePreset("7d")}
              style={buttonPresetStyle(selectedPreset === "7d")}
              disabled={loading}
            >
              7d
            </button>
            <button
              type="button"
              onClick={() => applyRangePreset("30d")}
              style={buttonPresetStyle(selectedPreset === "30d")}
              disabled={loading}
            >
              30d
            </button>
            <button
              type="button"
              onClick={() => applyRangePreset("month")}
              style={buttonPresetStyle(selectedPreset === "month")}
              disabled={loading}
            >
              Mês atual
            </button>
          </div>

          <div style={actionsRowStyle}>
            <button type="button" onClick={() => loadStatusAudit(0)} style={buttonWarnStyle} disabled={loading}>
              {loading ? "Consultando..." : "Consultar inconsistências"}
            </button>
            <button type="button" onClick={exportStatusAuditCsv} style={buttonStyle} disabled={loading}>
              {loading ? "Exportando..." : "Exportar CSV"}
            </button>
            <button
              type="button"
              onClick={() => loadStatusAudit(Math.max(statusOffset - statusLimit, 0))}
              style={buttonStyle}
              disabled={loading || statusOffset <= 0}
            >
              Página anterior
            </button>
            <button
              type="button"
              onClick={() => loadStatusAudit(statusOffset + statusLimit)}
              style={buttonStyle}
              disabled={loading || !statusHasMore}
            >
              Próxima página
            </button>
            <span style={{ color: "rgba(245,247,250,0.8)" }}>
              Offset atual: {statusOffset} | Itens nesta página: {statusAuditItems.length}
            </span>
          </div>
        </section>

        {error ? <pre style={errorStyle}>{error}</pre> : null}

        {!error && items.length > 0 ? (
          <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
            {items.map((item) => (
              <article key={item.id} style={rowStyle}>
                <div style={rowHeadStyle}>
                  <strong>{item.action || "-"}</strong>
                  <span style={badgeStyle(item.result)}>{item.result || "-"}</span>
                </div>
                <small style={smallStyle}>order_id: {item.order_id || "-"}</small>
                <small style={smallStyle}>user_id: {item.user_id || "-"}</small>
                <small style={smallStyle}>correlation_id: {item.correlation_id || "-"}</small>
                <small style={smallStyle}>created_at: {item.created_at || "-"}</small>
              </article>
            ))}
          </div>
        ) : null}

        {!error && statusAuditItems.length > 0 ? (
          <div style={{ marginTop: 16 }}>
            <h3 style={{ marginTop: 0 }}>Inconsistências de status</h3>
            <div style={{ display: "grid", gap: 10 }}>
              {statusAuditItems.map((item) => (
                <article key={`${item.order_id}-${item.reason}`} style={rowStyle}>
                  <div style={rowHeadStyle}>
                    <strong>{item.order_id}</strong>
                    <span style={badgeStyle("ERROR")}>ATENÇÃO</span>
                  </div>
                  <small style={smallStyle}>order_status: {item.order_status || "-"}</small>
                  <small style={smallStyle}>pickup_status: {item.pickup_status || "-"}</small>
                  <small style={smallStyle}>picked_up_at: {item.picked_up_at || "-"}</small>
                  <small style={smallStyle}>reason: {item.reason || "-"}</small>
                </article>
              ))}
            </div>
          </div>
        ) : null}

        {!error && !loading && items.length === 0 && statusAuditItems.length === 0 ? (
          <p style={{ marginTop: 14 }}>Nenhum evento encontrado com os filtros atuais.</p>
        ) : null}
      </section>
    </div>
  );
}

const pageStyle = {
  width: "100%",
  maxWidth: "none",
  padding: 24,
  boxSizing: "border-box",
  color: "#f5f7fa",
  fontFamily: "system-ui, sans-serif",
};

const cardStyle = {
  width: "100%",
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 16,
  padding: 16,
  boxSizing: "border-box",
};

const subCardStyle = {
  marginTop: 16,
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.02)",
  padding: 12,
};

const subtleTextStyle = {
  marginTop: 0,
  marginBottom: 8,
  color: "rgba(245,247,250,0.75)",
};

const mutedTextStyle = {
  color: "rgba(245, 247, 250, 0.8)",
  marginTop: 8,
  marginBottom: 0,
};

const shortcutRowStyle = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
  justifyContent: "flex-end",
  marginBottom: 10,
};

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

const filtersGridStyle = {
  marginTop: 14,
  display: "grid",
  gap: 10,
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
};

const labelStyle = {
  display: "grid",
  gap: 4,
  fontSize: 12,
  color: "rgba(245,247,250,0.86)",
};

const inputStyle = {
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const actionsRowStyle = {
  marginTop: 12,
  display: "flex",
  gap: 10,
  alignItems: "center",
  flexWrap: "wrap",
};

const buttonStyle = {
  padding: "8px 12px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "transparent",
  color: "#e2e8f0",
  fontWeight: 600,
};

const buttonWarnStyle = {
  ...buttonStyle,
  border: "1px solid rgba(245,158,11,0.55)",
  color: "#fde68a",
  background: "rgba(245,158,11,0.12)",
};

const buttonPresetStyle = (isActive) => ({
  ...buttonStyle,
  border: isActive ? "1px solid rgba(59,130,246,0.9)" : "1px solid rgba(96,165,250,0.5)",
  color: isActive ? "#dbeafe" : "#bfdbfe",
  background: isActive ? "rgba(59,130,246,0.28)" : "rgba(96,165,250,0.12)",
  padding: "6px 10px",
  fontSize: 12,
});

const buttonDangerStyle = {
  ...buttonStyle,
  border: "1px solid rgba(248,113,113,0.6)",
  color: "#fecaca",
  background: "rgba(127,29,29,0.25)",
};

const presetRowStyle = {
  marginTop: 8,
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
  alignItems: "center",
};

const presetLabelStyle = {
  color: "rgba(245,247,250,0.78)",
  fontSize: 12,
};

const errorStyle = {
  marginTop: 16,
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
  borderRadius: 12,
  overflow: "auto",
};

const rowStyle = {
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.03)",
  padding: 10,
  display: "grid",
  gap: 4,
};

const rowHeadStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
};

const smallStyle = {
  color: "rgba(226,232,240,0.9)",
  fontSize: 12,
  wordBreak: "break-word",
};

const badgeStyle = (result) => {
  const ok = String(result || "").toUpperCase() === "SUCCESS";
  return {
    display: "inline-flex",
    borderRadius: 999,
    padding: "4px 10px",
    fontSize: 12,
    fontWeight: 700,
    border: ok ? "1px solid rgba(31,122,63,0.65)" : "1px solid rgba(179,38,30,0.65)",
    background: ok ? "rgba(31,122,63,0.18)" : "rgba(179,38,30,0.20)",
    color: ok ? "#86efac" : "#fecaca",
  };
};

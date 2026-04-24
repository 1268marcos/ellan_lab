import React, { useMemo, useState } from "react";
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

export default function OpsAuditPage() {
  const { token } = useAuth();
  const now = new Date();
  const last72h = new Date(now.getTime() - 72 * 60 * 60 * 1000);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [limit, setLimit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [orderId, setOrderId] = useState("");
  const [action, setAction] = useState("");
  const [result, setResult] = useState("");
  const [auditFrom, setAuditFrom] = useState(toDateTimeLocalInputValue(last72h));
  const [auditTo, setAuditTo] = useState(toDateTimeLocalInputValue(now));
  const [statusLimit, setStatusLimit] = useState(200);
  const [statusOffset, setStatusOffset] = useState(0);
  const [statusHasMore, setStatusHasMore] = useState(false);
  const [statusAuditItems, setStatusAuditItems] = useState([]);

  const authHeaders = useMemo(() => {
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, [token]);

  async function loadAudit() {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      params.set("limit", String(Math.min(Math.max(Number(limit || 20), 1), 200)));
      params.set("offset", String(Math.max(Number(offset || 0), 0)));
      if (orderId.trim()) params.set("order_id", orderId.trim());
      if (action.trim()) params.set("action", action.trim());
      if (result.trim()) params.set("result", result.trim());

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
      setItems(Array.isArray(payload?.items) ? payload.items : []);
      setTotal(Number(payload?.total || 0));
    } catch (err) {
      setError(String(err?.message || err));
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }

  async function loadStatusAudit(nextOffset = null) {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const fromIso = toIsoOrNull(auditFrom);
      const toIso = toIsoOrNull(auditTo);
      if (!fromIso || !toIso) {
        throw new Error("Preencha from/to com datas válidas.");
      }

      const effectiveOffset = Math.max(Number(nextOffset ?? statusOffset ?? 0), 0);
      const effectiveLimit = Math.min(Math.max(Number(statusLimit || 200), 1), 2000);
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
              placeholder="2dd793dd-..."
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Action
            <input
              type="text"
              value={action}
              onChange={(event) => setAction(event.target.value)}
              placeholder="OPS_RECONCILE_ORDER"
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Result
            <input
              type="text"
              value={result}
              onChange={(event) => setResult(event.target.value)}
              placeholder="SUCCESS ou ERROR"
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Limit
            <input
              type="number"
              min={1}
              max={200}
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value || 20))}
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Offset
            <input
              type="number"
              min={0}
              value={offset}
              onChange={(event) => setOffset(Number(event.target.value || 0))}
              style={inputStyle}
            />
          </label>
        </div>

        <div style={actionsRowStyle}>
          <button type="button" onClick={loadAudit} style={buttonStyle} disabled={loading}>
            {loading ? "Consultando..." : "Consultar auditoria"}
          </button>
          <span style={{ color: "rgba(245,247,250,0.8)" }}>Total retornado: {total}</span>
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
                style={inputStyle}
              />
            </label>
            <label style={labelStyle}>
              To
              <input
                type="datetime-local"
                value={auditTo}
                onChange={(event) => setAuditTo(event.target.value)}
                style={inputStyle}
              />
            </label>
            <label style={labelStyle}>
              Limit
              <input
                type="number"
                min={1}
                max={2000}
                value={statusLimit}
                onChange={(event) => setStatusLimit(Number(event.target.value || 200))}
                style={inputStyle}
              />
            </label>
            <label style={labelStyle}>
              Offset
              <input
                type="number"
                min={0}
                value={statusOffset}
                onChange={(event) => setStatusOffset(Number(event.target.value || 0))}
                style={inputStyle}
              />
            </label>
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

        {!error && !loading && items.length === 0 ? (
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

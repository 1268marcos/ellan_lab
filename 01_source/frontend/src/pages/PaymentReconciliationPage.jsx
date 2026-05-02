import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

const RECON_STATUS_PRESETS = ["", "PENDING", "MATCHED", "MISMATCH", "MANUAL_REVIEW"];
const PAYMENT_STATUS_PRESETS = ["", "INITIATED", "PENDING", "APPROVED", "DECLINED", "REFUNDED", "ERROR"];
const SPLIT_STATUS_PRESETS = ["", "PENDING", "SETTLED", "FAILED", "CANCELLED"];

function parseError(payload, fallback = "Falha ao carregar conciliação de pagamentos.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) return payload.detail.message.trim();
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) return payload.detail.type.trim();
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

export default function PaymentReconciliationPage() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  const reconciliationStatus = searchParams.get("reconciliation_status") || "";
  const reconciliationBatchId = searchParams.get("reconciliation_batch_id") || "";
  const paymentStatus = searchParams.get("payment_status") || "";
  const splitStatus = searchParams.get("split_status") || "";
  const limit = Math.min(200, Math.max(1, Number(searchParams.get("limit")) || 50));
  const offset = Math.max(0, Number(searchParams.get("offset")) || 0);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState(null);

  const setFilters = useCallback(
    (patch) => {
      const next = new URLSearchParams(searchParams);
      Object.entries(patch).forEach(([k, v]) => {
        if (v === "" || v === undefined || v === null) next.delete(k);
        else next.set(k, String(v));
      });
      if (!("offset" in patch)) next.set("offset", "0");
      setSearchParams(next, { replace: true });
    },
    [searchParams, setSearchParams]
  );

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const qs = new URLSearchParams();
      if (reconciliationStatus.trim()) qs.set("reconciliation_status", reconciliationStatus.trim().toUpperCase());
      if (reconciliationBatchId.trim()) qs.set("reconciliation_batch_id", reconciliationBatchId.trim());
      if (paymentStatus.trim()) qs.set("payment_status", paymentStatus.trim().toUpperCase());
      if (splitStatus.trim()) qs.set("split_status", splitStatus.trim().toUpperCase());
      qs.set("limit", String(limit));
      qs.set("offset", String(offset));

      const r = await fetch(`${ORDER_PICKUP_BASE}/dev-admin/payment-reconciliation?${qs.toString()}`, {
        headers: { Accept: "application/json", ...authHeaders },
      });
      const json = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(json));
      setData(json);
    } catch (e) {
      setError(String(e?.message || e));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [
    token,
    authHeaders,
    reconciliationStatus,
    reconciliationBatchId,
    paymentStatus,
    splitStatus,
    limit,
    offset,
  ]);

  useEffect(() => {
    void load();
  }, [load]);

  const transactions = data?.transactions || [];
  const splits = data?.splits || [];
  const total = Number(data?.total || 0);
  const hasMore = Boolean(data?.has_more);

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Pagamentos — Conciliação (transações & splits)" />
        <p style={mutedTextStyle}>
          Dados de <code>payment_transactions</code> (<code>reconciliation_status</code>, <code>reconciliation_batch_id</code>) e{" "}
          <code>payment_splits</code> (<code>status</code>, <code>settled_at</code>) via{" "}
          <code>GET /dev-admin/payment-reconciliation</code>. Para compensação por pedido, use{" "}
          <Link to="/ops/reconciliation" style={linkStyle}>
            /ops/reconciliation
          </Link>
          .
        </p>

        <div style={filtersGridStyle}>
          <label style={labelStyle}>
            reconciliation_status
            <select
              style={inputStyle}
              value={reconciliationStatus}
              onChange={(e) => setFilters({ reconciliation_status: e.target.value })}
            >
              {RECON_STATUS_PRESETS.map((v) => (
                <option key={v || "ALL"} value={v}>
                  {v || "(todos)"}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            reconciliation_batch_id
            <input
              style={inputStyle}
              value={reconciliationBatchId}
              placeholder="ex.: batch-2026-05-01"
              onChange={(e) => setFilters({ reconciliation_batch_id: e.target.value })}
            />
          </label>
          <label style={labelStyle}>
            payment_transactions.status
            <select style={inputStyle} value={paymentStatus} onChange={(e) => setFilters({ payment_status: e.target.value })}>
              {PAYMENT_STATUS_PRESETS.map((v) => (
                <option key={v || "ALL"} value={v}>
                  {v || "(todos)"}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            payment_splits.status
            <select style={inputStyle} value={splitStatus} onChange={(e) => setFilters({ split_status: e.target.value })}>
              {SPLIT_STATUS_PRESETS.map((v) => (
                <option key={v || "ALL"} value={v}>
                  {v || "(todos)"}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div style={toolbarStyle}>
          <button type="button" style={buttonStyle} onClick={() => void load()} disabled={loading}>
            {loading ? "Carregando…" : "Atualizar"}
          </button>
          <span style={mutedTextStyle}>
            Total: <strong>{total}</strong>
            {data?.payment_splits_available === false ? (
              <>
                {" "}
                · <em>tabela payment_splits indisponível neste schema</em>
              </>
            ) : null}
          </span>
        </div>

        <div style={pagerStyle}>
          <button
            type="button"
            style={buttonGhostStyle}
            disabled={loading || offset <= 0}
            onClick={() => setFilters({ offset: String(Math.max(0, offset - limit)) })}
          >
            Página anterior
          </button>
          <button
            type="button"
            style={buttonGhostStyle}
            disabled={loading || !hasMore}
            onClick={() => setFilters({ offset: String(offset + limit) })}
          >
            Próxima página
          </button>
          <span style={metaStyle}>
            offset={offset} limit={limit}
          </span>
        </div>

        {error ? <pre style={errorStyle}>{error}</pre> : null}
      </section>

      <section style={cardStyle}>
        <h3 style={h3Style}>payment_transactions</h3>
        {transactions.length === 0 && !loading ? (
          <p style={mutedTextStyle}>Nenhuma transação para os filtros atuais.</p>
        ) : (
          <div style={tableWrapStyle}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>id</th>
                  <th style={thStyle}>order_id</th>
                  <th style={thStyle}>gateway</th>
                  <th style={thStyle}>status</th>
                  <th style={thStyle}>recon_status</th>
                  <th style={thStyle}>batch_id</th>
                  <th style={thStyle}>amount</th>
                  <th style={thStyle}>updated_at</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.id}</td>
                    <td style={tdStyle}>{row.order_id}</td>
                    <td style={tdStyle}>{row.gateway}</td>
                    <td style={tdStyle}>{row.status}</td>
                    <td style={tdStyle}>{row.reconciliation_status ?? "—"}</td>
                    <td style={tdStyle}>{row.reconciliation_batch_id ?? "—"}</td>
                    <td style={tdStyle}>{row.amount_cents}</td>
                    <td style={tdStyle}>{row.updated_at ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section style={cardStyle}>
        <h3 style={h3Style}>payment_splits (pedidos da página atual)</h3>
        {splits.length === 0 && !loading ? (
          <p style={mutedTextStyle}>Nenhum split retornado (ou nenhum pedido na página).</p>
        ) : (
          <div style={tableWrapStyle}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>id</th>
                  <th style={thStyle}>order_id</th>
                  <th style={thStyle}>recipient</th>
                  <th style={thStyle}>status</th>
                  <th style={thStyle}>amount</th>
                  <th style={thStyle}>settled_at</th>
                </tr>
              </thead>
              <tbody>
                {splits.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.id}</td>
                    <td style={tdStyle}>{row.order_id}</td>
                    <td style={tdStyle}>
                      {row.recipient_type}:{row.recipient_id}
                    </td>
                    <td style={tdStyle}>{row.status}</td>
                    <td style={tdStyle}>{row.amount_cents}</td>
                    <td style={tdStyle}>{row.settled_at ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
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
  marginBottom: 16,
};

const mutedTextStyle = {
  color: "rgba(245, 247, 250, 0.8)",
  marginTop: 0,
  marginBottom: 14,
  fontSize: 14,
  lineHeight: 1.45,
};

const labelStyle = { display: "grid", gap: 6, fontSize: 13 };

const inputStyle = {
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const filtersGridStyle = {
  display: "grid",
  gap: 12,
  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
  maxWidth: 960,
};

const toolbarStyle = { display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginTop: 8 };

const buttonStyle = {
  padding: "10px 16px",
  borderRadius: 10,
  border: "1px solid rgba(59,130,246,0.55)",
  background: "rgba(59,130,246,0.22)",
  color: "#e2e8f0",
  fontWeight: 700,
  cursor: "pointer",
};

const buttonGhostStyle = {
  ...buttonStyle,
  background: "transparent",
  border: "1px solid rgba(255,255,255,0.2)",
};

const pagerStyle = { display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap", marginTop: 12 };

const metaStyle = { color: "rgba(245,247,250,0.65)", fontSize: 13 };

const errorStyle = {
  marginTop: 12,
  padding: 12,
  borderRadius: 10,
  background: "rgba(127,29,29,0.35)",
  color: "#fecaca",
  whiteSpace: "pre-wrap",
};

const linkStyle = { color: "#93c5fd" };

const h3Style = { marginTop: 0, fontSize: 16 };

const tableWrapStyle = { overflowX: "auto", marginTop: 8 };

const tableStyle = { width: "100%", borderCollapse: "collapse", fontSize: 13 };

const thStyle = {
  textAlign: "left",
  padding: "8px 10px",
  borderBottom: "1px solid rgba(255,255,255,0.12)",
  color: "rgba(226,232,240,0.9)",
};

const tdStyle = {
  padding: "8px 10px",
  borderBottom: "1px solid rgba(255,255,255,0.06)",
  verticalAlign: "top",
  wordBreak: "break-all",
};

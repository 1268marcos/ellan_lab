import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";
const PAGE_VERSION = "ops/payments/reconciliation v0.2-health-shell";

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
    // eslint-disable-next-line react-hooks/set-state-in-effect -- refetch when URL/query changes
    void load();
  }, [load]);

  const transactions = data?.transactions || [];
  const splits = data?.splits || [];
  const total = Number(data?.total || 0);
  const hasMore = Boolean(data?.has_more);

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={crossShortcutStyle}>
          <Link to="/ops/health" style={crossShortcutLinkStyle}>
            Ir para saúde operacional
          </Link>
        </div>
        <div style={headerRowStyle}>
          <div>
            <OpsPageTitleHeader
              title="OPS — Pagamentos — Conciliação (transações & splits)"
              versionLabel={PAGE_VERSION}
              versionTo="/ops/auth/policy/versioning"
              containerStyle={{ marginBottom: 0 }}
              titleStyle={{ margin: 0 }}
            />
            <p style={mutedTextStyle}>
              Dados de <code style={{ color: "#e2e8f0" }}>payment_transactions</code> (
              <code style={{ color: "#e2e8f0" }}>reconciliation_status</code>, <code style={{ color: "#e2e8f0" }}>reconciliation_batch_id</code>) e{" "}
              <code style={{ color: "#e2e8f0" }}>payment_splits</code> (<code style={{ color: "#e2e8f0" }}>status</code>,{" "}
              <code style={{ color: "#e2e8f0" }}>settled_at</code>) via <code style={{ color: "#e2e8f0" }}>GET /dev-admin/payment-reconciliation</code>.
              Para compensação por pedido, use{" "}
              <Link to="/ops/reconciliation" style={gateDrilldownLinkStyle}>
                /ops/reconciliation
              </Link>
              .
            </p>
          </div>
          <div style={toolbarStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => void load()} disabled={loading}>
              {loading ? "Atualizando..." : "Atualizar"}
            </button>
          </div>
        </div>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Filtros</h3>
          </div>
          <div style={healthLocalFilterRowStyle}>
            <label style={healthLocalFilterFieldStyle}>
              reconciliation_status
              <select
                style={healthLocalFilterInputStyle}
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
            <label style={healthLocalFilterFieldStyle}>
              reconciliation_batch_id
              <input
                style={healthLocalFilterInputStyle}
                value={reconciliationBatchId}
                placeholder="ex.: batch-2026-05-01"
                onChange={(e) => setFilters({ reconciliation_batch_id: e.target.value })}
              />
            </label>
            <label style={healthLocalFilterFieldStyle}>
              payment_transactions.status
              <select style={healthLocalFilterInputStyle} value={paymentStatus} onChange={(e) => setFilters({ payment_status: e.target.value })}>
                {PAYMENT_STATUS_PRESETS.map((v) => (
                  <option key={v || "ALL"} value={v}>
                    {v || "(todos)"}
                  </option>
                ))}
              </select>
            </label>
            <label style={healthLocalFilterFieldStyle}>
              payment_splits.status
              <select style={healthLocalFilterInputStyle} value={splitStatus} onChange={(e) => setFilters({ split_status: e.target.value })}>
                {SPLIT_STATUS_PRESETS.map((v) => (
                  <option key={v || "ALL"} value={v}>
                    {v || "(todos)"}
                  </option>
                ))}
              </select>
            </label>
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
            <span style={summary24hHintStyle}>
              Total: <strong style={{ color: "#e2e8f0" }}>{total}</strong>
              {data?.payment_splits_available === false ? (
                <>
                  {" "}
                  · <em>tabela payment_splits indisponível neste schema</em>
                </>
              ) : null}
              {" · "}
              offset={offset} limit={limit}
            </span>
          </div>
        </section>

        {error ? (
          <div style={criticalBannerStyle} role="alert">
            {error}
          </div>
        ) : null}

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>payment_transactions</h3>
          </div>
          {transactions.length === 0 && !loading ? (
            <p style={{ ...summary24hHintStyle, margin: 0 }}>Nenhuma transação para os filtros atuais.</p>
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

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>payment_splits (pedidos da página atual)</h3>
          </div>
          {splits.length === 0 && !loading ? (
            <p style={{ ...summary24hHintStyle, margin: 0 }}>Nenhum split retornado (ou nenhum pedido na página).</p>
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

const headerRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 10,
  alignItems: "flex-start",
  flexWrap: "wrap",
};

const crossShortcutStyle = {
  display: "flex",
  justifyContent: "flex-end",
  marginBottom: 10,
};

const crossShortcutLinkStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(96,165,250,0.15)",
  color: "#bfdbfe",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 13,
};

const mutedTextStyle = {
  color: "rgba(245, 247, 250, 0.8)",
  marginTop: 8,
  marginBottom: 0,
};

const toolbarStyle = {
  display: "flex",
  gap: 10,
  alignItems: "flex-end",
  flexWrap: "wrap",
};

const labelStyle = {
  display: "grid",
  gap: 4,
  fontSize: 12,
  color: "rgba(245,247,250,0.86)",
};

const inputStyle = {
  width: 90,
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const healthLocalFilterRowStyle = {
  marginTop: 10,
  marginBottom: 8,
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  alignItems: "end",
};

const healthLocalFilterFieldStyle = {
  ...labelStyle,
  color: "#cbd5e1",
};

const healthLocalFilterInputStyle = {
  ...inputStyle,
  width: "100%",
  border: "1px solid rgba(148,163,184,0.5)",
};

const buttonGhostStyle = {
  padding: "8px 12px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "transparent",
  color: "#e2e8f0",
  fontWeight: 600,
};

const opsSanityCardStyle = {
  marginTop: 6,
  borderRadius: 12,
  border: "1px solid rgba(59,130,246,0.45)",
  background: "rgba(30,58,138,0.2)",
  padding: 12,
  display: "grid",
  gap: 10,
};

const summary24hHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const summary24hHintStyle = {
  color: "rgba(191,219,254,0.95)",
  fontSize: 11,
};

const gateDrilldownLinkStyle = {
  marginTop: 0,
  display: "inline",
  color: "#93c5fd",
  textDecoration: "underline",
  fontSize: 12,
  fontWeight: 600,
};

const pagerStyle = { display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap", marginTop: 4 };

const criticalBannerStyle = {
  borderRadius: 10,
  border: "1px solid rgba(248,113,113,0.72)",
  background: "linear-gradient(180deg, rgba(127,29,29,0.58) 0%, rgba(127,29,29,0.3) 100%)",
  color: "#fecaca",
  padding: "10px 12px",
  fontWeight: 700,
  fontSize: 13,
};

const tableWrapStyle = { overflowX: "auto" };

const tableStyle = { width: "100%", borderCollapse: "collapse", fontSize: 12 };

const thStyle = { textAlign: "left", borderBottom: "1px solid #444", padding: 8, color: "#cbd5e1" };

const tdStyle = { padding: 8, borderTop: "1px solid #333", color: "#e2e8f0", verticalAlign: "top", wordBreak: "break-all" };

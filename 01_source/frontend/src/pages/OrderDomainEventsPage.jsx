import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { getOrderLifecycleBase, olFetch } from "../utils/orderLifecycleInternalApi";

const PAGE_VERSION = "ops/order/domain-events v0.2-health-shell";

export default function OrderDomainEventsPage() {
  const [limit, setLimit] = useState(100);
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const cap = Math.min(500, Math.max(1, Number(limit) || 100));
      const j = await olFetch(`/internal/events/pending?limit=${cap}`);
      setItems(Array.isArray(j.items) ? j.items : []);
    } catch (e) {
      setError(e?.message || "Falha ao listar eventos pendentes");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- mount/refetch when limit changes
    void load();
  }, [load]);

  const cap = Math.min(500, Math.max(1, Number(limit) || 100));

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
              title="OPS — Order / domain events (pendentes)"
              versionLabel={PAGE_VERSION}
              versionTo="/ops/auth/policy/versioning"
              containerStyle={{ marginBottom: 0 }}
              titleStyle={{ margin: 0 }}
            />
            <p style={mutedTextStyle}>
              <code style={{ color: "#e2e8f0" }}>GET /internal/events/pending</code> em{" "}
              <code style={{ color: "#e2e8f0" }}>{getOrderLifecycleBase()}</code>. Token opcional:{" "}
              <code style={{ color: "#e2e8f0" }}>VITE_INTERNAL_TOKEN</code>.
            </p>
          </div>
          <div style={toolbarStyle}>
            <label style={labelStyle}>
              limit
              <input
                type="number"
                min={1}
                max={500}
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value) || 100)}
                style={inputStyle}
              />
            </label>
            <button type="button" onClick={() => void load()} disabled={loading} style={buttonGhostStyle}>
              {loading ? "Atualizando..." : "Carregar"}
            </button>
          </div>
        </div>

        {error ? (
          <div style={criticalBannerStyle} role="alert">
            {error}
          </div>
        ) : null}

        {!loading && !error ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Resumo</h3>
            </div>
            <div style={summary24hGridStyle}>
              <article style={summary24hItemStyle}>
                <strong style={summary24hValueStyle}>{items.length}</strong>
                <small style={summary24hLabelStyle}>itens</small>
              </article>
              <article style={summary24hItemStyle}>
                <strong style={{ ...summary24hValueStyle, fontSize: 13 }}>{cap}</strong>
                <small style={summary24hLabelStyle}>limit efetivo</small>
              </article>
            </div>
          </section>
        ) : null}

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Eventos pendentes</h3>
          </div>
          <div style={{ overflow: "auto", maxHeight: "70vh" }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["event_key", "aggregate", "event_name", "status", "created_at"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={row.id || row.event_key}>
                    <td style={tdStyle}>{row.event_key}</td>
                    <td style={tdStyle}>
                      {row.aggregate_type}:{row.aggregate_id}
                    </td>
                    <td style={tdStyle}>{row.event_name}</td>
                    <td style={tdStyle}>{row.status}</td>
                    <td style={{ ...tdStyle, fontFamily: "ui-monospace, monospace", fontSize: 11 }}>
                      {String(row.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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

const summary24hGridStyle = {
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
};

const summary24hItemStyle = {
  borderRadius: 10,
  border: "1px solid rgba(148,163,184,0.3)",
  background: "rgba(15,23,42,0.35)",
  padding: "8px 10px",
  display: "grid",
  gap: 2,
};

const summary24hValueStyle = {
  color: "#f8fafc",
  fontSize: 18,
  fontWeight: 800,
};

const summary24hLabelStyle = {
  color: "#cbd5e1",
  fontSize: 12,
};

const criticalBannerStyle = {
  borderRadius: 10,
  border: "1px solid rgba(248,113,113,0.72)",
  background: "linear-gradient(180deg, rgba(127,29,29,0.58) 0%, rgba(127,29,29,0.3) 100%)",
  color: "#fecaca",
  padding: "10px 12px",
  fontWeight: 700,
  fontSize: 13,
};

const tableStyle = { width: "100%", borderCollapse: "collapse", fontSize: 12 };
const thStyle = { textAlign: "left", borderBottom: "1px solid #444", padding: 8, color: "#cbd5e1" };
const tdStyle = { padding: 8, borderTop: "1px solid #333", color: "#e2e8f0" };

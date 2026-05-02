import React, { useCallback, useEffect, useState } from "react";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { getOrderLifecycleBase, olFetch } from "../utils/orderLifecycleInternalApi";

const PAGE_VERSION = "ops/order/domain-events v0.1";

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
    load();
  }, [load]);

  return (
    <div className="ops-page" style={{ padding: "1rem", maxWidth: 1200 }}>
      <OpsPageTitleHeader title="OPS — Order / domain events (pendentes)" versionLabel={PAGE_VERSION} />
      <p style={{ opacity: 0.85, marginBottom: 12 }}>
        <code>GET /internal/events/pending</code> em <code>{getOrderLifecycleBase()}</code>. Token opcional:{" "}
        <code>VITE_INTERNAL_TOKEN</code>.
      </p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center", marginBottom: 12 }}>
        <label>
          limit{" "}
          <input
            type="number"
            min={1}
            max={500}
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value) || 100)}
            style={{ width: 80 }}
          />
        </label>
        <button type="button" onClick={load} disabled={loading}>
          {loading ? "Carregando…" : "Carregar"}
        </button>
      </div>
      {error ? <p style={{ color: "#f87171" }}>{error}</p> : null}
      {!loading && !error ? (
        <p style={{ fontSize: 13 }}>
          itens={items.length} limit={Math.min(500, Math.max(1, Number(limit) || 100))}
        </p>
      ) : null}
      <div style={{ overflow: "auto", maxHeight: "70vh" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr>
              {["event_key", "aggregate", "event_name", "status", "created_at"].map((h) => (
                <th key={h} style={{ textAlign: "left", borderBottom: "1px solid #444", padding: 4 }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map((row) => (
              <tr key={row.id || row.event_key}>
                <td style={{ padding: 4, borderTop: "1px solid #333" }}>{row.event_key}</td>
                <td style={{ padding: 4, borderTop: "1px solid #333" }}>
                  {row.aggregate_type}:{row.aggregate_id}
                </td>
                <td style={{ padding: 4, borderTop: "1px solid #333" }}>{row.event_name}</td>
                <td style={{ padding: 4, borderTop: "1px solid #333" }}>{row.status}</td>
                <td style={{ padding: 4, borderTop: "1px solid #333", fontFamily: "ui-monospace, monospace", fontSize: 11 }}>
                  {String(row.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

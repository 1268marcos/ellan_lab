import React, { useCallback, useState } from "react";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { olFetch } from "../utils/orderLifecycleInternalApi";

export default function OrderDomainEventsPage() {
  const [items, setItems] = useState([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const j = await olFetch("/internal/events/pending?limit=100");
      setItems(Array.isArray(j.items) ? j.items : []);
    } catch (e) {
      setErr(e?.message || String(e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <OpsPageTitleHeader title="Domain events — pendentes" subtitle="GET /internal/events/pending" />
      <button type="button" onClick={load} disabled={loading} style={{ marginTop: 12 }}>
        {loading ? "Carregando…" : "Listar pendentes"}
      </button>
      {err ? <p style={{ color: "#f87171", marginTop: 12 }}>{err}</p> : null}
      <table style={{ width: "100%", marginTop: 16, borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr>
            {["event_key", "aggregate", "event_name", "status", "created_at"].map((h) => (
              <th key={h} style={{ textAlign: "left", borderBottom: "1px solid #444", padding: 6 }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((row) => (
            <tr key={row.id || row.event_key}>
              <td style={{ padding: 6, borderTop: "1px solid #333" }}>{row.event_key}</td>
              <td style={{ padding: 6, borderTop: "1px solid #333" }}>
                {row.aggregate_type}:{row.aggregate_id}
              </td>
              <td style={{ padding: 6, borderTop: "1px solid #333" }}>{row.event_name}</td>
              <td style={{ padding: 6, borderTop: "1px solid #333" }}>{row.status}</td>
              <td style={{ padding: 6, borderTop: "1px solid #333" }}>{String(row.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

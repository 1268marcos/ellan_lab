import React, { useCallback, useEffect, useState } from "react";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { fetchRuntimeJson } from "../utils/runtimeOpsApi";

const INTERNAL = import.meta.env.VITE_INTERNAL_TOKEN || "";
const DEFAULT_MACHINE = import.meta.env.VITE_RUNTIME_MACHINE_ID || "CACIFO-XX-001";

export default function OpsRuntimeEventLogPage() {
  const [machineId, setMachineId] = useState(DEFAULT_MACHINE);
  const [limit, setLimit] = useState(100);
  const [rows, setRows] = useState([]);
  const [meta, setMeta] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const q = new URLSearchParams({ machine_id: machineId.trim(), limit: String(limit) });
      const headers = {};
      if (INTERNAL) headers["X-Internal-Token"] = INTERNAL;
      const data = await fetchRuntimeJson(`/audit/events?${q}`, { headers });
      setMeta(data);
      setRows(Array.isArray(data?.events) ? data.events : []);
    } catch (e) {
      setError(e?.message || "Falha ao listar eventos");
      setRows([]);
      setMeta(null);
    } finally {
      setLoading(false);
    }
  }, [machineId, limit]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="ops-page" style={{ padding: "1rem", maxWidth: 1200 }}>
      <OpsPageTitleHeader title="OPS — Runtime / events" versionLabel="ops/runtime/events v0.1" />
      <p style={{ opacity: 0.85, marginBottom: 12 }}>
        SQLite append-only via <code>/api/rt/audit/events</code>. Token interno opcional:{" "}
        <code>VITE_INTERNAL_TOKEN</code>.
      </p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center", marginBottom: 12 }}>
        <label>
          machine_id{" "}
          <input value={machineId} onChange={(e) => setMachineId(e.target.value)} style={{ minWidth: 220 }} />
        </label>
        <label>
          limit{" "}
          <input
            type="number"
            min={1}
            max={2000}
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
      {meta && !error ? (
        <p style={{ fontSize: 13 }}>
          returned={meta.returned} machine_id={meta.machine_id}
        </p>
      ) : null}
      <div style={{ overflow: "auto", maxHeight: "70vh" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr>
              {["id", "ts", "door", "type", "severity", "hash"].map((h) => (
                <th key={h} style={{ textAlign: "left", borderBottom: "1px solid #444", padding: 4 }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.event_id}>
                <td style={{ padding: 4 }}>{r.event_id}</td>
                <td style={{ padding: 4 }}>{r.ts}</td>
                <td style={{ padding: 4 }}>{r.door_id}</td>
                <td style={{ padding: 4 }}>{r.event_type}</td>
                <td style={{ padding: 4 }}>{r.severity}</td>
                <td style={{ padding: 4, fontFamily: "monospace", fontSize: 10 }}>{String(r.hash || "").slice(0, 18)}…</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

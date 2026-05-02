import React, { useCallback, useEffect, useState } from "react";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import OpsActionButton from "../components/OpsActionButton";
import RuntimeOpsSubnav from "../components/RuntimeOpsSubnav";
import { fetchRuntimeJson, formatRuntimeFetchError } from "../utils/runtimeOpsApi";
import {
  actionsStyle,
  cardStyle,
  errorStyle,
  filtersStyle,
  inputStyle,
  labelStyle,
  metaLineStyle,
  mutedStyle,
  pageStyle,
  tableStyle,
  tableWrapStyle,
  tdStyle,
  thStyle,
  monoTdStyle,
} from "../utils/runtimeOpsPageChrome";

const PAGE_VERSION = "ops/runtime/events v0.2";
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
      setError(formatRuntimeFetchError(e));
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
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Runtime / events" versionLabel={PAGE_VERSION} />
        <RuntimeOpsSubnav />
        <p style={mutedStyle}>
          Append-only SQLite via <code style={{ color: "#E2E8F0" }}>/api/rt/audit/events</code>. Se o runtime exigir,
          envie <code>VITE_INTERNAL_TOKEN</code> (header <code>X-Internal-Token</code>).
        </p>
        <div style={filtersStyle}>
          <label style={labelStyle}>
            machine_id
            <input value={machineId} onChange={(e) => setMachineId(e.target.value)} style={inputStyle} />
          </label>
          <label style={labelStyle}>
            limit
            <input
              type="number"
              min={1}
              max={2000}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value) || 100)}
              style={inputStyle}
            />
          </label>
        </div>
        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void load()} disabled={loading}>
            {loading ? "Carregando…" : "Carregar eventos"}
          </OpsActionButton>
        </div>
        {error ? <div style={errorStyle}>{error}</div> : null}
        {meta && !error ? (
          <p style={metaLineStyle}>
            returned={meta.returned} machine_id={meta.machine_id}
            {meta.door_id != null ? ` door_id=${meta.door_id}` : ""}
          </p>
        ) : null}
        <div style={tableWrapStyle}>
          <table style={tableStyle}>
            <thead>
              <tr>
                {["id", "ts", "door", "type", "severity", "hash"].map((h) => (
                  <th key={h} style={thStyle}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.event_id}>
                  <td style={tdStyle}>{r.event_id}</td>
                  <td style={monoTdStyle}>{r.ts}</td>
                  <td style={tdStyle}>{r.door_id}</td>
                  <td style={tdStyle}>{r.event_type}</td>
                  <td style={tdStyle}>{r.severity}</td>
                  <td style={monoTdStyle}>{String(r.hash || "").slice(0, 22)}…</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

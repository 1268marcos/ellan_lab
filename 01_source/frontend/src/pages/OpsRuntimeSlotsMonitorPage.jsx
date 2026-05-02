import React, { useCallback, useEffect, useState } from "react";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { fetchRuntimeJson } from "../utils/runtimeOpsApi";

export default function OpsRuntimeSlotsMonitorPage() {
  const [lockerId, setLockerId] = useState("");
  const [slots, setSlots] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const headers = {};
      const lid = lockerId.trim();
      if (lid) headers["X-Locker-Id"] = lid;
      const data = await fetchRuntimeJson("/locker/slots", { headers });
      setSlots(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e?.message || "Falha ao listar slots");
      setSlots([]);
    } finally {
      setLoading(false);
    }
  }, [lockerId]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="ops-page" style={{ padding: "1rem", maxWidth: 960 }}>
      <OpsPageTitleHeader title="OPS — Runtime / slots" versionLabel="ops/runtime/slots v0.1" />
      <p style={{ opacity: 0.85, marginBottom: 12 }}>
        GET <code>/api/rt/locker/slots</code>. Header opcional <code>X-Locker-Id</code>.
      </p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center", marginBottom: 12 }}>
        <label>
          X-Locker-Id{" "}
          <input value={lockerId} onChange={(e) => setLockerId(e.target.value)} placeholder="(resolver default)" style={{ minWidth: 240 }} />
        </label>
        <button type="button" onClick={load} disabled={loading}>
          {loading ? "Carregando…" : "Atualizar"}
        </button>
      </div>
      {error ? <p style={{ color: "#f87171" }}>{error}</p> : null}
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr>
            {["slot", "state", "product_id", "updated_at"].map((h) => (
              <th key={h} style={{ textAlign: "left", borderBottom: "1px solid #444", padding: 6 }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {slots.map((s) => (
            <tr key={s.slot}>
              <td style={{ padding: 6 }}>{s.slot}</td>
              <td style={{ padding: 6 }}>{s.state}</td>
              <td style={{ padding: 6 }}>{s.product_id || "—"}</td>
              <td style={{ padding: 6 }}>{s.updated_at}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

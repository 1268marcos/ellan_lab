
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
} from "../utils/runtimeOpsPageChrome";

const PAGE_VERSION = "ops/runtime/slots v0.2";

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
      setError(formatRuntimeFetchError(e));
      setSlots([]);
    } finally {
      setLoading(false);
    }
  }, [lockerId]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Runtime / slots" versionLabel={PAGE_VERSION} />
        <RuntimeOpsSubnav />
        <p style={mutedStyle}>
          <strong>GET</strong> <code style={{ color: "#E2E8F0" }}>/api/rt/locker/slots</code>. Header opcional{" "}
          <code>X-Locker-Id</code> para resolver o locker; vazio usa o resolver padrão do runtime.
        </p>
        <div style={filtersStyle}>
          <label style={labelStyle}>
            X-Locker-Id (opcional)
            <input
              value={lockerId}
              onChange={(e) => setLockerId(e.target.value)}
              style={inputStyle}
              placeholder="Resolver default do runtime"
            />
          </label>
        </div>
        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void load()} disabled={loading}>
            {loading ? "Carregando…" : "Atualizar slots"}
          </OpsActionButton>
        </div>
        {error ? <div style={errorStyle}>{error}</div> : null}
        {!loading && !error ? <p style={metaLineStyle}>slots={slots.length}</p> : null}
        <div style={tableWrapStyle}>
          <table style={tableStyle}>
            <thead>
              <tr>
                {["slot", "state", "product_id", "updated_at"].map((h) => (
                  <th key={h} style={thStyle}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {slots.map((s) => (
                <tr key={s.slot}>
                  <td style={tdStyle}>{s.slot}</td>
                  <td style={tdStyle}>{s.state}</td>
                  <td style={tdStyle}>{s.product_id || "—"}</td>
                  <td style={tdStyle}>{s.updated_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}


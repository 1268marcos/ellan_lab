import React, { useCallback, useEffect, useState } from "react";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { lockersOpsApi } from "../api/lockersOpsApi";
import { cardStyle, pageStyle, tableStyle, tdStyle, thStyle } from "../styles/opsShellStyles";

export default function OpsSlaReportsPage() {
  const [sla, setSla] = useState([]);
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    setErr("");
    try {
      const data = await lockersOpsApi.getAlerts({ alert_type: "SLA_BREACH", limit: 500 });
      setSla(data.items || []);
    } catch (e) {
      setErr(String(e.message || e));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const open = sla.filter((a) => !a.resolved_at);

  return (
    <div style={pageStyle}>
      <OpsPageTitleHeader title="SLA Reports" />
      {err ? <p style={{ color: "#f87171" }}>{err}</p> : null}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12, marginBottom: 16 }}>
        <div style={cardStyle}>
          <p>Total</p>
          <strong>{sla.length}</strong>
        </div>
        <div style={cardStyle}>
          <p>Abertos</p>
          <strong>{open.length}</strong>
        </div>
        <div style={cardStyle}>
          <p>Resolvidos</p>
          <strong>{sla.length - open.length}</strong>
        </div>
      </div>
      <table style={tableStyle}>
        <thead>
          <tr>
            <th style={thStyle}>Severidade</th>
            <th style={thStyle}>Locker</th>
            <th style={thStyle}>Tipo</th>
            <th style={thStyle}>Detectado</th>
          </tr>
        </thead>
        <tbody>
          {sla.map((a) => (
            <tr key={a.alert_id}>
              <td style={tdStyle}>{a.severity}</td>
              <td style={tdStyle}>{a.locker_display_name}</td>
              <td style={tdStyle}>{a.breach_type}</td>
              <td style={tdStyle}>{new Date(a.detected_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

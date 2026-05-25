import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { lockersOpsApi, opsRealtimeWsUrl } from "../api/lockersOpsApi";
import { cardStyle, pageStyle } from "../styles/opsShellStyles";

export default function OpsNocAlertsPage() {
  const [items, setItems] = useState([]);
  const [connected, setConnected] = useState(false);
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    setErr("");
    try {
      const data = await lockersOpsApi.getAlerts({ limit: 200 });
      setItems(data.items || []);
    } catch (e) {
      setErr(String(e.message || e));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const ws = new WebSocket(opsRealtimeWsUrl("/ws/ops/alerts"));
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === "alerts_critical" && msg.items?.length) {
          setItems((prev) => {
            const ids = new Set(msg.items.map((a) => a.alert_id));
            return [...msg.items, ...prev.filter((p) => !ids.has(p.alert_id))].slice(0, 200);
          });
        }
      } catch {
        /* */
      }
    };
    return () => ws.close();
  }, []);

  return (
    <div style={pageStyle}>
      <OpsPageTitleHeader title="NOC Alerts" subtitle={connected ? "Live" : "Offline"} />
      {err ? <p style={{ color: "#f87171" }}>{err}</p> : null}
      <ul style={{ listStyle: "none", padding: 0 }}>
        {items.map((a) => (
          <li key={`${a.alert_type}-${a.alert_id}`} style={{ ...cardStyle, marginBottom: 8 }}>
            <span style={{ color: "#f87171", fontWeight: 600 }}>{a.severity}</span> · {a.alert_type}
            <p style={{ margin: "4px 0" }}>{a.locker_display_name || a.reference_id}</p>
            <p style={{ fontSize: 12, color: "#94a3b8" }}>{a.breach_type}</p>
            {a.reference_id ? <Link to={`/ops/lockers/${a.reference_id}`}>Ver locker</Link> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

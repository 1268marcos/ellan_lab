import React from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function OpsTelemetryChart({ points, hours = 24 }) {
  const data = (points || []).map((p) => ({
    t: new Date(p.occurred_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    temp: p.temperature_celsius != null ? Number(p.temperature_celsius) : null,
    battery: p.battery_pct != null ? Number(p.battery_pct) : null,
    signal: p.signal_rssi != null ? Number(p.signal_rssi) : null,
  }));
  if (!data.length) {
    return <p style={{ color: "#94a3b8", fontSize: 13 }}>Sem telemetria nas últimas {hours}h.</p>;
  }
  return (
    <div style={{ height: 280, width: "100%" }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="t" tick={{ fontSize: 10 }} stroke="#94a3b8" />
          <YAxis yAxisId="left" tick={{ fontSize: 10 }} stroke="#94a3b8" />
          <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10 }} stroke="#94a3b8" />
          <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
          <Legend />
          <Line yAxisId="left" type="monotone" dataKey="temp" name="°C" stroke="#38bdf8" dot={false} />
          <Line yAxisId="left" type="monotone" dataKey="battery" name="Bateria %" stroke="#34d399" dot={false} />
          <Line yAxisId="right" type="monotone" dataKey="signal" name="RSSI" stroke="#fbbf24" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

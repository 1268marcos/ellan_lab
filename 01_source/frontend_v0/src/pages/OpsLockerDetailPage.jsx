import React, { useCallback, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import OpsHealthScoreCard from "../components/ops/OpsHealthScoreCard";
import OpsOccupancyGauge from "../components/ops/OpsOccupancyGauge";
import OpsTelemetryChart from "../components/ops/OpsTelemetryChart";
import { lockersOpsApi, opsRealtimeWsUrl } from "../api/lockersOpsApi";
import { buttonPrimaryStyle, pageStyle, tabButtonStyle } from "../styles/opsShellStyles";

const TABS = ["overview", "telemetry", "maintenance", "pickups"];

export default function OpsLockerDetailPage() {
  const { id } = useParams();
  const [search, setSearch] = useSearchParams();
  const tab = TABS.includes(search.get("tab")) ? search.get("tab") : "overview";
  const [locker, setLocker] = useState(null);
  const [telemetry, setTelemetry] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [pickups, setPickups] = useState([]);
  const [title, setTitle] = useState("");
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    if (!id) return;
    setErr("");
    try {
      const [lk, tel, maint, pick] = await Promise.all([
        lockersOpsApi.getLocker(id),
        lockersOpsApi.getTelemetry(id, 48),
        lockersOpsApi.getMaintenance(id),
        lockersOpsApi.getPickups(id),
      ]);
      setLocker(lk);
      setTelemetry(tel.items || []);
      setTickets(maint.items || []);
      setPickups(pick.items || []);
    } catch (e) {
      setErr(String(e.message || e));
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!id) return undefined;
    const ws = new WebSocket(opsRealtimeWsUrl("/ws/ops/realtime"));
    ws.onopen = () => ws.send(JSON.stringify({ type: "subscribe", locker_ids: [id] }));
    return () => ws.close();
  }, [id]);

  const createTicket = async () => {
    if (!title.trim()) return;
    await lockersOpsApi.createMaintenance(id, { title: title.trim() });
    setTitle("");
    const m = await lockersOpsApi.getMaintenance(id);
    setTickets(m.items || []);
  };

  return (
    <div style={pageStyle}>
      <Link to="/ops/lockers/map">← Mapa</Link>
      <OpsPageTitleHeader title={locker?.display_name || id} />
      {err ? <p style={{ color: "#f87171" }}>{err}</p> : null}
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            style={{ ...tabButtonStyle, ...(tab === t ? { background: "#4f46e5", color: "#fff" } : {}) }}
            onClick={() => setSearch({ tab: t })}
          >
            {t}
          </button>
        ))}
      </div>
      {tab === "overview" && locker ? (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <OpsHealthScoreCard score={locker.health_score} status={locker.health_status} lastTelemetryAt={locker.last_telemetry_at} />
          <OpsOccupancyGauge pct={locker.occupancy_pct} level={locker.occupancy_level} />
        </div>
      ) : null}
      {tab === "telemetry" ? <OpsTelemetryChart points={telemetry} hours={48} /> : null}
      {tab === "maintenance" ? (
        <div>
          <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Título" style={{ flex: 1, padding: 8 }} />
            <button type="button" style={buttonPrimaryStyle} onClick={createTicket}>
              Abrir ticket
            </button>
          </div>
          <ul>
            {tickets.map((t) => (
              <li key={t.id} style={{ marginBottom: 8 }}>
                {t.title} — {t.status} ({t.priority})
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {tab === "pickups" ? (
        <ul>
          {pickups.map((p) => (
            <li key={p.order_id}>
              {p.order_id} · {p.status} · slot {p.slot_label || "—"}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

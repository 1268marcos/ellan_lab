import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { lockersOpsApi, opsRealtimeWsUrl } from "../api/lockersOpsApi";
import { buttonPrimaryStyle, cardStyle, pageStyle, tableStyle, tdStyle, thStyle } from "../styles/opsShellStyles";

const COLORS = { healthy: "#22c55e", warning: "#f59e0b", critical: "#ef4444", offline: "#64748b", unknown: "#94a3b8" };

function icon(status) {
  const c = COLORS[status] || COLORS.unknown;
  return L.divIcon({
    className: "",
    html: `<span style="display:block;width:14px;height:14px;border-radius:50%;background:${c};border:2px solid #fff"></span>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

export default function OpsLockersMapPage() {
  const mapRef = useRef(null);
  const mapInst = useRef(null);
  const [rows, setRows] = useState([]);
  const [region, setRegion] = useState("");
  const [q, setQ] = useState("");
  const [err, setErr] = useState("");
  const [liveN, setLiveN] = useState(0);

  const load = useCallback(async () => {
    setErr("");
    try {
      const params = {};
      if (region) params.region = region;
      if (q) params.q = q;
      const data = await lockersOpsApi.listLockers(params);
      setRows(data.items || []);
    } catch (e) {
      setErr(String(e.message || e));
    }
  }, [region, q]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const ws = new WebSocket(opsRealtimeWsUrl("/ws/ops/realtime"));
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.items) setLiveN(msg.items.length);
      } catch {
        /* */
      }
    };
    return () => ws.close();
  }, []);

  const withCoords = useMemo(() => rows.filter((r) => r.latitude != null && r.longitude != null), [rows]);

  useEffect(() => {
    if (!mapRef.current || !withCoords.length) return undefined;
    if (mapInst.current) {
      mapInst.current.remove();
      mapInst.current = null;
    }
    const lats = withCoords.map((r) => r.latitude);
    const lons = withCoords.map((r) => r.longitude);
    const map = L.map(mapRef.current).setView(
      [(Math.min(...lats) + Math.max(...lats)) / 2, (Math.min(...lons) + Math.max(...lons)) / 2],
      11,
    );
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);
    const layer = L.layerGroup().addTo(map);
    withCoords.forEach((lk) => {
      layer.addLayer(
        L.marker([lk.latitude, lk.longitude], { icon: icon(lk.ops_status) }).bindPopup(
          `<strong>${lk.display_name || lk.id}</strong><br/><a href="/v0/ops/lockers/${lk.id}">Detalhe</a>`,
        ),
      );
    });
    map.fitBounds(L.latLngBounds(withCoords.map((r) => [r.latitude, r.longitude])), { padding: [24, 24] });
    mapInst.current = map;
    return () => {
      map.remove();
      mapInst.current = null;
    };
  }, [withCoords]);

  return (
    <div style={pageStyle}>
      <OpsPageTitleHeader title="Lockers Map" subtitle={`${withCoords.length} no mapa · ${liveN} live`} />
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        <input value={region} onChange={(e) => setRegion(e.target.value)} placeholder="Região" style={{ padding: 8 }} />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar" style={{ padding: 8, minWidth: 180 }} />
        <button type="button" style={buttonPrimaryStyle} onClick={load}>
          Filtrar
        </button>
        <Link to="/ops/maintenance">Manutenção</Link>
        <Link to="/ops/noc-alerts">NOC</Link>
      </div>
      {err ? <p style={{ color: "#f87171" }}>{err}</p> : null}
      <div ref={mapRef} style={{ height: 480, borderRadius: 12, border: "1px solid #334155" }} />
      <div style={{ ...cardStyle, marginTop: 16, overflowX: "auto" }}>
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>Locker</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Ocupação</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td style={tdStyle}>
                  <Link to={`/ops/lockers/${r.id}`}>{r.display_name || r.id}</Link>
                </td>
                <td style={tdStyle}>{r.ops_status}</td>
                <td style={tdStyle}>{r.occupancy_pct != null ? `${Number(r.occupancy_pct).toFixed(1)}%` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

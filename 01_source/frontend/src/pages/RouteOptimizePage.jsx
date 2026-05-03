import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import FiscalPageLayout from "../components/FiscalPageLayout";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { mlIntelligenceApi } from "../api/mlIntelligenceClient";

/** Mapa Leaflet: rota depósito (centróide) → lockers otimizada. */
export default function RouteOptimizePage() {
  const location = useLocation();
  const isOps = location.pathname.startsWith("/ops/");
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layerRef = useRef(null);

  const [rawIds, setRawIds] = useState("");
  const [capacity, setCapacity] = useState(80);
  const [twStart, setTwStart] = useState(8 * 60);
  const [twEnd, setTwEnd] = useState(20 * 60);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [res, setRes] = useState(null);

  const baseOk = useMemo(() => Boolean(mlIntelligenceApi.baseUrl()), []);

  const lockerIds = useMemo(
    () =>
      rawIds
        .split(/[\s,;\n]+/)
        .map((s) => s.trim())
        .filter(Boolean),
    [rawIds]
  );

  const run = useCallback(async () => {
    if (lockerIds.length < 2) {
      setErr("Informe ao menos dois locker_id (separados por vírgula ou linha).");
      return;
    }
    if (!baseOk) {
      setErr("Configure VITE_ML_PREDICTOR_BASE_URL.");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      const body = await mlIntelligenceApi.optimizeRoute({
        locker_ids: lockerIds,
        vehicle_capacity_parcels: capacity,
        time_window_start_minutes: twStart,
        time_window_end_minutes: twEnd,
      });
      setRes(body);
    } catch (e) {
      setErr(String(e.message || e));
      setRes(null);
    } finally {
      setBusy(false);
    }
  }, [lockerIds, capacity, twStart, twEnd, baseOk]);

  useEffect(() => {
    if (!res?.lockers_meta?.length || !mapRef.current) return undefined;
    const meta = res.lockers_meta;
    const depot = res.depot;
    const ordered = res.ordered_locker_ids || [];
    const byId = Object.fromEntries(meta.map((m) => [m.locker_id, m]));

    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
      layerRef.current = null;
    }

    const lats = meta.map((m) => m.lat).concat(depot?.lat != null ? [depot.lat] : []);
    const lons = meta.map((m) => m.lon).concat(depot?.lon != null ? [depot.lon] : []);
    const midLat = lats.reduce((a, b) => a + b, 0) / lats.length;
    const midLon = lons.reduce((a, b) => a + b, 0) / lons.length;

    const map = L.map(mapRef.current, { zoomControl: true }).setView([midLat, midLon], 12);
    mapInstanceRef.current = map;
    const group = L.layerGroup().addTo(map);
    layerRef.current = group;

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap",
      maxZoom: 19,
    }).addTo(map);

    if (depot?.lat != null && depot?.lon != null) {
      L.circleMarker([depot.lat, depot.lon], { radius: 10, color: "#a78bfa", fillColor: "#7c3aed", fillOpacity: 0.85 })
        .bindPopup("Depósito (centróide)")
        .addTo(group);
    }

    meta.forEach((m) => {
      const isFirst = ordered[0] === m.locker_id;
      L.circleMarker([m.lat, m.lon], {
        radius: isFirst ? 8 : 6,
        color: "#38bdf8",
        fillColor: isFirst ? "#0ea5e9" : "#0369a1",
        fillOpacity: 0.9,
      })
        .bindPopup(`${m.locker_id}<br/>pendentes: ${m.pending_deliveries ?? 0}`)
        .addTo(group);
    });

    const pathLatLngs = [];
    if (depot?.lat != null) pathLatLngs.push([depot.lat, depot.lon]);
    ordered.forEach((id) => {
      const m = byId[id];
      if (m) pathLatLngs.push([m.lat, m.lon]);
    });
    if (depot?.lat != null && pathLatLngs.length > 1) pathLatLngs.push([depot.lat, depot.lon]);

    if (pathLatLngs.length >= 2) {
      L.polyline(pathLatLngs, { color: "#f472b6", weight: 3, opacity: 0.9 }).addTo(group);
    }

    const b = group.getBounds();
    if (b.isValid()) map.fitBounds(b.pad(0.12));

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [res]);

  const subtitle = isOps
    ? "OPS · K-means + RF (tempo) + OR-Tools VRP — POST /logistics/optimize-route"
    : "Inteligência · mesma API — redução típica de km 15–20% vs ordem de entrada";

  return (
    <FiscalPageLayout>
      <div className="intel-ml-surface ops-page">
        <OpsPageTitleHeader title="Roteirização ML (lockers)" subtitle={subtitle} />

        {!baseOk ? <p className="intel-ml-error">Defina VITE_ML_PREDICTOR_BASE_URL no build do frontend.</p> : null}

        <div className="intel-ml-card intel-ml-card--toolbar" style={{ flexWrap: "wrap", gap: 10, alignItems: "flex-end" }}>
          <label className="intel-ml-field" style={{ flex: "2 1 280px" }}>
            <span className="intel-ml-fieldLabel">locker_ids (vírgula ou linha)</span>
            <textarea
              className="intel-ml-input"
              rows={4}
              value={rawIds}
              onChange={(e) => setRawIds(e.target.value)}
              style={{ width: "100%", marginTop: 4, fontFamily: "monospace", fontSize: 12 }}
              placeholder="id-locker-1&#10;id-locker-2"
            />
          </label>
          <label className="intel-ml-field" style={{ flex: "0 1 100px" }}>
            <span className="intel-ml-fieldLabel">Capacidade</span>
            <input
              type="number"
              min={1}
              max={500}
              className="intel-ml-input"
              value={capacity}
              onChange={(e) => setCapacity(Number(e.target.value) || 80)}
              style={{ width: "100%", marginTop: 4 }}
            />
          </label>
          <label className="intel-ml-field" style={{ flex: "0 1 90px" }}>
            <span className="intel-ml-fieldLabel">TW início (min)</span>
            <input
              type="number"
              className="intel-ml-input"
              value={twStart}
              onChange={(e) => setTwStart(Number(e.target.value) || 0)}
              style={{ width: "100%", marginTop: 4 }}
            />
          </label>
          <label className="intel-ml-field" style={{ flex: "0 1 90px" }}>
            <span className="intel-ml-fieldLabel">TW fim (min)</span>
            <input
              type="number"
              className="intel-ml-input"
              value={twEnd}
              onChange={(e) => setTwEnd(Number(e.target.value) || 0)}
              style={{ width: "100%", marginTop: 4 }}
            />
          </label>
          <button type="button" disabled={busy} className="intel-ml-btn intel-ml-btn--primary" onClick={() => void run()}>
            {busy ? "Otimizando…" : "Otimizar rota"}
          </button>
        </div>

        {err ? <p className="intel-ml-error">{err}</p> : null}

        {res ? (
          <>
            <div className="intel-ml-card" style={{ marginTop: 14 }}>
              <p className="intel-ml-pageSub" style={{ marginBottom: 8 }}>
                km ingênuo (ordem de entrada): <strong>{res.total_km_naive_haversine}</strong> · otimizado:{" "}
                <strong>{res.total_km_optimized_haversine}</strong> · redução:{" "}
                <strong>{res.reduction_pct_vs_input_order}%</strong> · faixa típica operacional:{" "}
                <strong>{res.estimated_reduction_band_typical}</strong>
              </p>
              <p className="intel-ml-pageSub" style={{ fontSize: 11 }}>
                Clusters K-means: {res.k_clusters} · visita: {res.ordered_locker_ids?.join(" → ")}
              </p>
            </div>
            <div
              ref={mapRef}
              style={{
                height: 420,
                marginTop: 14,
                borderRadius: 12,
                border: "1px solid var(--fiscal-card-border)",
                overflow: "hidden",
              }}
            />
          </>
        ) : (
          <p className="intel-ml-pageSub" style={{ marginTop: 12 }}>
            Informe lockers com coordenadas no banco. Restrições: capacidade do veículo, janela de duração da rota,
            prioridade via prazos em <span className="intel-ml-code">inbound_deliveries</span>.
          </p>
        )}
      </div>
    </FiscalPageLayout>
  );
}

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import FiscalPageLayout from "../components/FiscalPageLayout";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { mlIntelligenceApi } from "../api/mlIntelligenceClient";

const OPS_ROUTE_VERSION = "ops/logistics/route-optimize v0.2-health-shell";

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

  const intelSubtitle = "Inteligência · mesma API — redução típica de km 15–20% vs ordem de entrada";
  const opsMuted =
    "OPS · K-means + RF (tempo) + OR-Tools VRP — POST /logistics/optimize-route. Configure VITE_ML_PREDICTOR_BASE_URL no build do frontend.";

  if (isOps) {
    return (
      <div style={pageStyle}>
        <section style={cardStyle}>
          <div style={crossShortcutStyle}>
            <Link to="/ops/health" style={crossShortcutLinkStyle}>
              Ir para saúde operacional
            </Link>
          </div>
          <div style={headerRowStyle}>
            <div>
              <OpsPageTitleHeader
                title="Roteirização ML (lockers)"
                versionLabel={OPS_ROUTE_VERSION}
                versionTo="/ops/auth/policy/versioning"
                containerStyle={{ marginBottom: 0 }}
                titleStyle={{ margin: 0 }}
              />
              <p style={mutedTextStyle}>{opsMuted}</p>
            </div>
          </div>

          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Parâmetros</h3>
            </div>
            <label style={{ ...healthLocalFilterFieldStyle, gridColumn: "1 / -1" }}>
              locker_ids (vírgula ou linha)
              <textarea
                rows={4}
                value={rawIds}
                onChange={(e) => setRawIds(e.target.value)}
                style={textareaStyle}
                placeholder={"id-locker-1\nid-locker-2"}
              />
            </label>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                Capacidade
                <input
                  type="number"
                  min={1}
                  max={500}
                  value={capacity}
                  onChange={(e) => setCapacity(Number(e.target.value) || 80)}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                TW início (min)
                <input
                  type="number"
                  value={twStart}
                  onChange={(e) => setTwStart(Number(e.target.value) || 0)}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                TW fim (min)
                <input
                  type="number"
                  value={twEnd}
                  onChange={(e) => setTwEnd(Number(e.target.value) || 0)}
                  style={healthLocalFilterInputStyle}
                />
              </label>
            </div>
            <div style={toolbarStyle}>
              <button type="button" disabled={busy} style={buttonGhostStyle} onClick={() => void run()}>
                {busy ? "Atualizando..." : "Otimizar rota"}
              </button>
            </div>
          </section>

          {!baseOk ? <p style={summary24hHintStyle}>Defina VITE_ML_PREDICTOR_BASE_URL no build do frontend.</p> : null}

          {err ? (
            <div style={criticalBannerStyle} role="alert">
              {err}
            </div>
          ) : null}

          {res ? (
            <>
              <section style={opsSanityCardStyle}>
                <div style={summary24hHeaderStyle}>
                  <h3 style={{ margin: 0, fontSize: 14 }}>Resultado</h3>
                </div>
                <p style={{ ...summary24hHintStyle, margin: 0, lineHeight: 1.55 }}>
                  km ingênuo (ordem de entrada): <strong style={{ color: "#e2e8f0" }}>{res.total_km_naive_haversine}</strong> · otimizado:{" "}
                  <strong style={{ color: "#e2e8f0" }}>{res.total_km_optimized_haversine}</strong> · redução:{" "}
                  <strong style={{ color: "#e2e8f0" }}>{res.reduction_pct_vs_input_order}%</strong> · faixa típica operacional:{" "}
                  <strong style={{ color: "#e2e8f0" }}>{res.estimated_reduction_band_typical}</strong>
                </p>
                <p style={{ ...summary24hHintStyle, margin: 0 }}>
                  Clusters K-means: {res.k_clusters} · visita: {res.ordered_locker_ids?.join(" → ")}
                </p>
              </section>
              <div
                ref={mapRef}
                style={{
                  height: 420,
                  marginTop: 6,
                  borderRadius: 10,
                  border: "1px solid rgba(255,255,255,0.14)",
                  overflow: "hidden",
                  background: "#0b0f14",
                }}
              />
            </>
          ) : (
            <section style={opsSanityCardStyle}>
              <p style={{ ...summary24hHintStyle, margin: 0, lineHeight: 1.55 }}>
                Informe lockers com coordenadas no banco. Restrições: capacidade do veículo, janela de duração da rota, prioridade via prazos em{" "}
                <code style={{ color: "#e2e8f0" }}>inbound_deliveries</code>.
              </p>
            </section>
          )}
        </section>
      </div>
    );
  }

  return (
    <FiscalPageLayout>
      <div className="intel-ml-surface ops-page">
        <OpsPageTitleHeader title="Roteirização ML (lockers)" subtitle={intelSubtitle} />

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

const pageStyle = {
  width: "100%",
  maxWidth: "none",
  padding: 24,
  boxSizing: "border-box",
  color: "#f5f7fa",
  fontFamily: "system-ui, sans-serif",
};

const cardStyle = {
  width: "100%",
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 16,
  padding: 16,
  boxSizing: "border-box",
};

const headerRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 10,
  alignItems: "flex-start",
  flexWrap: "wrap",
};

const crossShortcutStyle = {
  display: "flex",
  justifyContent: "flex-end",
  marginBottom: 10,
};

const crossShortcutLinkStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(96,165,250,0.15)",
  color: "#bfdbfe",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 13,
};

const mutedTextStyle = {
  color: "rgba(245, 247, 250, 0.8)",
  marginTop: 8,
  marginBottom: 0,
};

const labelStyle = {
  display: "grid",
  gap: 4,
  fontSize: 12,
  color: "rgba(245,247,250,0.86)",
};

const inputStyle = {
  width: 90,
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const healthLocalFilterFieldStyle = {
  ...labelStyle,
  color: "#cbd5e1",
};

const healthLocalFilterRowStyle = {
  marginTop: 10,
  marginBottom: 8,
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  alignItems: "end",
};

const healthLocalFilterInputStyle = {
  ...inputStyle,
  width: "100%",
  border: "1px solid rgba(148,163,184,0.5)",
};

const textareaStyle = {
  ...healthLocalFilterInputStyle,
  minHeight: 88,
  resize: "vertical",
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
  fontSize: 12,
};

const toolbarStyle = {
  display: "flex",
  gap: 10,
  alignItems: "flex-end",
  flexWrap: "wrap",
};

const buttonGhostStyle = {
  padding: "8px 12px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "transparent",
  color: "#e2e8f0",
  fontWeight: 600,
};

const opsSanityCardStyle = {
  marginTop: 6,
  borderRadius: 12,
  border: "1px solid rgba(59,130,246,0.45)",
  background: "rgba(30,58,138,0.2)",
  padding: 12,
  display: "grid",
  gap: 10,
};

const summary24hHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const summary24hHintStyle = {
  color: "rgba(191,219,254,0.95)",
  fontSize: 11,
};

const criticalBannerStyle = {
  borderRadius: 10,
  border: "1px solid rgba(248,113,113,0.72)",
  background: "linear-gradient(180deg, rgba(127,29,29,0.58) 0%, rgba(127,29,29,0.3) 100%)",
  color: "#fecaca",
  padding: "10px 12px",
  fontWeight: 700,
  fontSize: 13,
};

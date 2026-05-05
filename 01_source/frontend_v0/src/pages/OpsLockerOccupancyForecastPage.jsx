
import React, { useCallback, useMemo, useState } from "react";
import FiscalPageLayout from "../components/FiscalPageLayout";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { mlIntelligenceApi } from "../api/mlIntelligenceClient";

const ML_BASE = () => mlIntelligenceApi.baseUrl();

/** Heatmap alinhado ao tema fiscal: ciano → índigo → rosa perigo */
function heatStyle(pct) {
  const p = Math.max(0, Math.min(100, pct));
  if (p < 50) {
    const a = 0.28 + p / 280;
    return { background: `linear-gradient(165deg, rgba(34,211,238,${a}), rgba(99,102,241,0.12))` };
  }
  if (p < 75) {
    const a = 0.32 + (p - 50) / 120;
    return { background: `linear-gradient(165deg, rgba(99,102,241,${a}), rgba(167,139,250,0.15))` };
  }
  const a = 0.38 + (p - 75) / 90;
  return { background: `linear-gradient(165deg, rgba(244,63,94,${Math.min(0.82, a)}), rgba(99,102,241,0.18))` };
}

function heatTextClass(pct) {
  if (pct < 55) return "intel-ml-heatCell--textLow";
  if (pct < 82) return "intel-ml-heatCell--textMid";
  return "intel-ml-heatCell--textHigh";
}

export default function OpsLockerOccupancyForecastPage() {
  const [lockerId, setLockerId] = useState("");
  const [hours, setHours] = useState(24);
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const baseOk = useMemo(() => Boolean(ML_BASE()), []);

  const load = useCallback(async () => {
    const lid = String(lockerId || "").trim();
    if (!lid) {
      setErr("Informe o locker_id.");
      return;
    }
    if (!baseOk) {
      setErr("Configure VITE_ML_PREDICTOR_BASE_URL (ml_predictor_service).");
      return;
    }
    setLoading(true);
    setErr("");
    try {
      const u = `${ML_BASE()}/ops/lockers/${encodeURIComponent(lid)}/occupancy-forecast?hours=${hours}`;
      const r = await fetch(u, { headers: { Accept: "application/json" } });
      const t = await r.text();
      let body;
      try {
        body = t ? JSON.parse(t) : null;
      } catch {
        body = { raw: t };
      }
      if (!r.ok) throw new Error(body?.detail || body?.error || `${r.status}`);
      setData(body);
    } catch (e) {
      setErr(String(e.message || e));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [lockerId, hours, baseOk]);

  const fc = data?.forecast || [];
  const alerts = data?.alerts || [];
  const nCols = Math.min(fc.length, 24);

  return (
    <FiscalPageLayout>
      <div className="intel-ml-surface ops-page">
        <OpsPageTitleHeader title="Previsão de ocupação (slots)" subtitle="Heatmap + alertas ≥85% por 3h — ml_predictor_service" />

        {!baseOk ? <p className="intel-ml-error">Defina VITE_ML_PREDICTOR_BASE_URL no build do frontend.</p> : null}

        <div className="intel-ml-card intel-ml-card--toolbar">
          <label className="intel-ml-field">
            <span className="intel-ml-fieldLabel">locker_id</span>
            <input className="intel-ml-input" value={lockerId} onChange={(e) => setLockerId(e.target.value)} />
          </label>
          <label className="intel-ml-field">
            <span className="intel-ml-fieldLabel">horas</span>
            <select className="intel-ml-select" value={hours} onChange={(e) => setHours(Number(e.target.value))}>
              {[6, 12, 18, 24].map((h) => (
                <option key={h} value={h}>
                  {h}h
                </option>
              ))}
            </select>
          </label>
          <button type="button" disabled={loading} className="intel-ml-btn intel-ml-btn--primary" onClick={() => void load()}>
            {loading ? "Carregando…" : "Atualizar previsão"}
          </button>
        </div>

        {err ? <p className="intel-ml-error">{err}</p> : null}

        {alerts.length > 0 ? (
          <div className="intel-ml-alert" role="alert">
            <strong>Alertas automáticos</strong> — ocupação prevista ≥ 85% por ≥3h seguidas:
            <ul>
              {alerts.map((a, i) => (
                <li key={i}>
                  horas índice {a.from_hour_index}–{a.to_hour_index} (pico {Math.round((a.peak_occupancy_fraction || 0) * 100)}%)
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {data ? (
          <>
            <div className="intel-ml-metaRow">
              Modelo: <span className="intel-ml-code">{data.model}</span>
              <span style={{ marginLeft: 12 }}>slots totais: {fc[0]?.slots_total ?? "—"}</span>
            </div>
            <p className="intel-ml-heatLabel">Heatmap — ocupação prevista (% slots)</p>
            <div className="intel-ml-heatGrid" style={{ gridTemplateColumns: `repeat(${nCols}, minmax(0, 1fr))` }}>
              {fc.map((cell, idx) => {
                const pct = Number(cell.occupied_pct_slots) || 0;
                return (
                  <div
                    key={idx}
                    className={`intel-ml-heatCell ${heatTextClass(pct)}`}
                    title={`${cell.hour_start}\n${pct.toFixed(1)}%`}
                    style={heatStyle(pct)}
                  >
                    <span style={{ fontWeight: 700 }}>{pct.toFixed(0)}%</span>
                    <span style={{ opacity: 0.9 }}>+{idx + 1}h</span>
                  </div>
                );
              })}
            </div>
            <div className="intel-ml-tableWrap">
              <table className="intel-ml-table">
                <thead>
                  <tr>
                    <th className="intel-ml-th">hora (UTC)</th>
                    <th className="intel-ml-th">% ocupação</th>
                    <th className="intel-ml-th">slots est.</th>
                  </tr>
                </thead>
                <tbody>
                  {fc.map((cell, idx) => (
                    <tr key={idx}>
                      <td className="intel-ml-td" style={{ fontFamily: "ui-monospace, monospace" }}>
                        {String(cell.hour_start).slice(0, 16)}
                      </td>
                      <td className="intel-ml-td">{cell.occupied_pct_slots}</td>
                      <td className="intel-ml-td">{cell.occupied_slots_est}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : null}
      </div>
    </FiscalPageLayout>
  );
}


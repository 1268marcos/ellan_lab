
import React, { useCallback, useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import OpsActionButton from "../components/OpsActionButton";
import {
  actionsStyle,
  cardStyle,
  errorStyle,
  metaLineStyle,
  mutedStyle,
  pageStyle,
  preJsonStyle,
  tableStyle,
  tableWrapStyle,
  tdStyle,
  thStyle,
} from "../utils/runtimeOpsPageChrome";
import { mlIntelligenceApi } from "../api/mlIntelligenceClient";

const mlBase = () => mlIntelligenceApi.baseUrl();
const PAGE_VERSION = "ops/intelligence v0.2";

export default function OpsIntelligencePage() {
  const [dash, setDash] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [trainOut, setTrainOut] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);

  const loadDash = useCallback(async () => {
    setError("");
    try {
      const r = await fetch(`${mlBase()}/ml/dashboard`);
      if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
      setDash(await r.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setDash(null);
    }
  }, []);

  const loadMetrics = useCallback(async () => {
    try {
      const r = await fetch(`${mlBase()}/metrics`);
      if (r.ok) setMetrics(await r.json());
      else setMetrics(null);
    } catch {
      setMetrics(null);
    }
  }, []);

  const loadAll = useCallback(async () => {
    setLoading(true);
    await Promise.all([loadDash(), loadMetrics()]);
    setLoading(false);
  }, [loadDash, loadMetrics]);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  const forceTrain = async () => {
    setTraining(true);
    setTrainOut(null);
    setError("");
    try {
      const r = await fetch(`${mlBase()}/ml/train`, { method: "POST" });
      const body = await r.json();
      setTrainOut(body);
      if (!r.ok || body.ok === false) {
        setError(body.error || `train failed ${r.status}`);
      }
      await loadAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setTraining(false);
    }
  };

  const atRisk = dash?.at_risk_lockers || [];
  const series = (dash?.avg_health_score_series || []).map((s) => ({
    d: String(s.d),
    avg_health_score: Number(s.avg_health_score) || 0,
  }));
  const topDoors = dash?.top_door_failures_70d || [];

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Intelligence (ML)" versionLabel={PAGE_VERSION} />
        <p style={mutedStyle}>
          API <code style={{ color: "#E2E8F0" }}>{mlBase()}</code> —{" "}
          <code>VITE_ML_PREDICTOR_BASE_URL</code> (dev: omissão → <code>/api/ml</code> via proxy)
        </p>
        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void loadAll()} disabled={loading}>
            {loading ? "Carregando…" : "Atualizar"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="warn" onClick={() => void forceTrain()} disabled={training}>
            {training ? "Treinando…" : "Forçar retreino (POST /ml/train)"}
          </OpsActionButton>
        </div>
        {error ? <div style={errorStyle}>{error}</div> : null}
        {trainOut ? <pre style={preJsonStyle}>{JSON.stringify(trainOut, null, 2)}</pre> : null}
        {metrics ? (
          <p style={metaLineStyle}>
            Modelo ativo: <strong style={{ color: "#E2E8F0" }}>{metrics.model_version}</strong> —{" "}
            <code style={{ color: "#94A3B8", fontSize: 12 }}>{JSON.stringify(metrics.metrics)}</code>
          </p>
        ) : (
          <p style={mutedStyle}>Sem /metrics (treine o modelo primeiro).</p>
        )}
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
        <section style={{ ...cardStyle, margin: 0 }}>
          <div style={{ fontSize: 12, color: "#94A3B8" }}>Em risco</div>
          <div style={{ fontSize: 28, fontWeight: 800, color: "#f87171" }}>{atRisk.length}</div>
          <div style={{ fontSize: 11, color: "#64748B" }}>health &lt; 30 e bateria 70d ≤ 20</div>
        </section>
        <section style={{ ...cardStyle, margin: 0 }}>
          <div style={{ fontSize: 12, color: "#94A3B8" }}>Média health (último dia na série)</div>
          <div style={{ fontSize: 28, fontWeight: 800, color: "#34d399" }}>
            {series.length ? series[series.length - 1].avg_health_score.toFixed(1) : "—"}
          </div>
        </section>
        <section style={{ ...cardStyle, margin: 0 }}>
          <div style={{ fontSize: 12, color: "#94A3B8" }}>Top door_failures (1º)</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: "#E2E8F0" }}>
            {topDoors[0] ? `${topDoors[0].door_failures_70d}` : "—"}
          </div>
        </section>
      </div>

      <section style={{ ...cardStyle, marginTop: 4 }}>
        <h2 style={{ marginTop: 0, fontSize: "1.05rem", color: "#F1F5F9" }}>
          Health score médio diário (7 dias)
        </h2>
        {series.length === 0 ? (
          <p style={mutedStyle}>Sem predições no período.</p>
        ) : (
          <div style={{ width: "100%", height: 240 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={series} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="d" tick={{ fill: "#94A3B8", fontSize: 11 }} stroke="#475569" />
                <YAxis domain={[0, 100]} tick={{ fill: "#94A3B8", fontSize: 11 }} stroke="#475569" />
                <Tooltip
                  contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }}
                  labelStyle={{ color: "#E2E8F0" }}
                />
                <Line type="monotone" dataKey="avg_health_score" stroke="#38bdf8" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      <section style={{ ...cardStyle, marginTop: 4 }}>
        <h2 style={{ marginTop: 0, fontSize: "1.05rem", color: "#F1F5F9" }}>
          Lockers em risco (tabela)
        </h2>
        {atRisk.length === 0 ? (
          <p style={mutedStyle}>Nenhum locker no critério.</p>
        ) : (
          <div style={tableWrapStyle}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>locker_id</th>
                  <th style={thStyle}>health_score</th>
                  <th style={thStyle}>battery_min (70d)</th>
                  <th style={thStyle}>door_failures_70d</th>
                </tr>
              </thead>
              <tbody>
                {atRisk.map((row) => (
                  <tr key={row.locker_id}>
                    <td style={tdStyle}>{row.locker_id}</td>
                    <td style={tdStyle}>{Number(row.health_score).toFixed(1)}</td>
                    <td style={tdStyle}>{row.battery_min != null ? Number(row.battery_min).toFixed(1) : "—"}</td>
                    <td style={tdStyle}>{row.door_failures_70d ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section style={{ ...cardStyle, marginTop: 4 }}>
        <h2 style={{ marginTop: 0, fontSize: "1.05rem", color: "#F1F5F9" }}>Top 10 door_failures_70d</h2>
        {topDoors.length === 0 ? (
          <p style={mutedStyle}>Sem dados.</p>
        ) : (
          <ol style={{ color: "#CBD5E1", fontSize: 13, paddingLeft: 20 }}>
            {topDoors.map((r) => (
              <li key={r.locker_id}>
                <strong style={{ color: "#E2E8F0" }}>{r.locker_id}</strong> — {r.door_failures_70d}
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}


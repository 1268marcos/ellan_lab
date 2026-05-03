import React, { useCallback, useEffect, useState } from "react";
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
} from "../utils/runtimeOpsPageChrome";

const ML_BASE = import.meta.env.VITE_ML_PREDICTOR_BASE_URL || "http://localhost:8047";
const PAGE_VERSION = "ops/intelligence v0.1";

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
      const r = await fetch(`${ML_BASE}/intelligence/dashboard?days=30`);
      if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
      setDash(await r.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setDash(null);
    }
  }, []);

  const loadMetrics = useCallback(async () => {
    try {
      const r = await fetch(`${ML_BASE}/metrics`);
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
      const r = await fetch(`${ML_BASE}/train`, { method: "POST" });
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

  const series = dash?.series || [];
  const maxP = Math.max(0.001, ...series.map((s) => Number(s.avg_failure_p) || 0));

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Inteligência (ML)" versionLabel={PAGE_VERSION} />
        <p style={mutedStyle}>
          API <code style={{ color: "#E2E8F0" }}>{ML_BASE}</code> — configure{" "}
          <code>VITE_ML_PREDICTOR_BASE_URL</code>.
        </p>
        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void loadAll()} disabled={loading}>
            {loading ? "Carregando…" : "Atualizar"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="warn" onClick={() => void forceTrain()} disabled={training}>
            {training ? "Treinando…" : "Forçar retreinamento"}
          </OpsActionButton>
        </div>
        {error ? <div style={errorStyle}>{error}</div> : null}
        {trainOut ? <pre style={preJsonStyle}>{JSON.stringify(trainOut, null, 2)}</pre> : null}
        {metrics ? (
          <p style={metaLineStyle}>
            Modelo ativo: {metrics.model_version} — métricas:{" "}
            <code style={{ color: "#E2E8F0" }}>{JSON.stringify(metrics.metrics)}</code>
          </p>
        ) : (
          <p style={mutedStyle}>Sem métricas (rode treino após seed).</p>
        )}
      </section>

      <section style={{ ...cardStyle, marginTop: 16 }}>
        <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Lockers em risco (última predição, health &lt; 30)</h2>
        {dash?.at_risk?.length ? (
          <ul style={{ paddingLeft: 18 }}>
            {dash.at_risk.map((row) => (
              <li key={row.locker_id}>
                <strong>{row.locker_id}</strong> — health {Number(row.health_score).toFixed(1)} — p_fail{" "}
                {(Number(row.failure_probability) * 100).toFixed(1)}%
              </li>
            ))}
          </ul>
        ) : (
          <p style={mutedStyle}>Nenhum locker abaixo do limiar (ou ainda sem predições).</p>
        )}
      </section>

      <section style={{ ...cardStyle, marginTop: 16 }}>
        <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Histórico de predições (média p_fail por dia)</h2>
        {series.length === 0 ? (
          <p style={mutedStyle}>Sem pontos no log ainda.</p>
        ) : (
          <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 140, marginTop: 8 }}>
            {series.map((s) => {
              const h = Math.round((60 + (Number(s.avg_failure_p) / maxP) * 80) * 10) / 10;
              return (
                <div key={String(s.d)} style={{ flex: 1, minWidth: 4, textAlign: "center" }}>
                  <div
                    title={`${s.d}: ${s.avg_failure_p}`}
                    style={{
                      height: `${h}px`,
                      background: "#3B82F6",
                      borderRadius: 2,
                      marginBottom: 4,
                    }}
                  />
                  <div style={{ fontSize: 10, color: "#94A3B8" }}>{String(s.d).slice(5)}</div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

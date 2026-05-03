import React, { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import FiscalPageLayout from "../../components/FiscalPageLayout";
import { useAuth } from "../../context/AuthContext";
import { mlIntelligenceApi } from "../../api/mlIntelligenceClient";

const G = {
  background: "var(--fiscal-card-bg)",
  border: "1px solid var(--fiscal-card-border)",
  borderRadius: 14,
  padding: 16,
  color: "var(--fiscal-soft-text)",
  boxShadow: "0 4px 20px rgba(2, 6, 23, 0.32)",
};
const H = { fontSize: 14, fontWeight: 700, margin: "0 0 10px", color: "var(--fiscal-text)" };
const TBL = { width: "100%", borderCollapse: "collapse", fontSize: 12 };
const TH = { textAlign: "left", padding: 8, borderBottom: "1px solid var(--fiscal-table-separator-strong)", color: "var(--fiscal-muted)" };
const TD = { padding: 8, borderTop: "1px solid var(--fiscal-table-separator-soft)", color: "var(--fiscal-soft-text)" };

function Card({ title, children }) {
  return (
    <div style={G}>
      <h3 style={H}>{title}</h3>
      {children}
    </div>
  );
}

export function InteligenciaDashboardPage() {
  const { hasRole } = useAuth();
  const canTrain = hasRole("admin_operacao");
  const [d, setD] = useState(null);
  const [rng, setRng] = useState(30);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    mlIntelligenceApi.dashboard().then(setD).catch((e) => setMsg(String(e.message || e)));
  }, []);
  const series = useMemo(() => (rng === 7 ? d?.avg_health_score_series_7d : d?.avg_health_score_series_30d) || [], [d, rng]);
  const train = async () => {
    setBusy(true);
    setMsg("");
    try {
      const o = await mlIntelligenceApi.train();
      setMsg(o.ok ? `OK ${o.model_version || ""}` : o.error || "falhou");
      setD(await mlIntelligenceApi.dashboard());
    } catch (e) {
      setMsg(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <FiscalPageLayout>
      <div style={{ padding: 20, display: "grid", gap: 14, maxWidth: 1200, margin: "0 auto" }}>
        <h1 style={{ color: "#f1f5f9", fontSize: 22 }}>Dashboard ML</h1>
        {msg ? <p style={{ color: "#f87171" }}>{msg}</p> : null}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: 10 }}>
          <Card title="Lockers em risco">{d ? <b style={{ fontSize: 26 }}>{d.at_risk_count}</b> : "…"}</Card>
          <Card title="Modelo ativo">{d?.active_model?.model_version || "—"}</Card>
          <Card title="Última predição">{d?.last_prediction_at ? String(d.last_prediction_at).slice(0, 19) : "—"}</Card>
          <Card title="Acurácia (ativo)">{d?.active_accuracy != null ? Number(d.active_accuracy).toFixed(4) : "—"}</Card>
        </div>
        <div style={{ ...G, display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ color: "#94a3b8", fontSize: 13 }}>Série health médio:</span>
          {[7, 30].map((n) => (
            <button key={n} type="button" onClick={() => setRng(n)} style={{ padding: "6px 12px", borderRadius: 8, border: rng === n ? "1px solid #38bdf8" : "1px solid #475569", background: rng === n ? "rgba(56,189,248,0.15)" : "#0f172a", color: "#e2e8f0", cursor: "pointer" }}>
              {n}d
            </button>
          ))}
          {canTrain ? (
            <button type="button" disabled={busy} onClick={() => void train()} style={{ marginLeft: "auto", padding: "8px 14px", borderRadius: 10, background: "#7c3aed", color: "#fff", border: "none", cursor: busy ? "wait" : "pointer" }}>
              {busy ? "Treinando…" : "Forçar treinamento"}
            </button>
          ) : null}
        </div>
        <div style={{ ...G, height: 400 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={series}>
              <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
              <XAxis dataKey="d" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
              <Line type="monotone" dataKey="avg_health_score" stroke="#38bdf8" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <Card title="Top 5 pior health_score">
          <table style={TBL}>
            <thead>
              <tr>
                <th style={TH}>locker</th>
                <th style={TH}>health</th>
                <th style={TH}>p_fail</th>
              </tr>
            </thead>
            <tbody>
              {(d?.top5_worst_health || []).map((r) => (
                <tr key={r.locker_id}>
                  <td style={TD}>{r.locker_id}</td>
                  <td style={TD}>{r.health_score != null ? Number(r.health_score).toFixed(1) : ""}</td>
                  <td style={TD}>{r.failure_probability != null ? Number(r.failure_probability).toFixed(3) : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </FiscalPageLayout>
  );
}

export function ModelMonitorPage() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    mlIntelligenceApi.models().then(setD).catch((e) => setErr(String(e.message || e)));
  }, []);
  const rows = d?.models || [];
  return (
    <FiscalPageLayout>
      <div style={{ padding: 20, maxWidth: 900, margin: "0 auto", color: "#e2e8f0" }}>
        <h1 style={{ fontSize: 22 }}>Monitor de modelos</h1>
        {d?.drift_delta_accuracy_vs_previous != null ? (
          <p style={{ color: "#a78bfa", fontSize: 13 }}>Δ acurácia vs versão anterior: {Number(d.drift_delta_accuracy_vs_previous).toFixed(4)}</p>
        ) : null}
        {err ? <p style={{ color: "#f87171" }}>{err}</p> : null}
        <div style={{ display: "grid", gap: 10 }}>
          {rows.map((m) => (
            <div key={m.model_version} style={{ ...G, borderColor: m.status === "ACTIVE" ? "#38bdf8" : "#334155" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <strong>{m.model_version}</strong>
                <span style={{ color: m.status === "ACTIVE" ? "#38bdf8" : "#94a3b8" }}>{m.status}</span>
              </div>
              <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 6 }}>{m.trained_at ? String(m.trained_at) : ""}</div>
              <pre style={{ fontSize: 11, marginTop: 8, overflow: "auto", color: "#cbd5e1" }}>{JSON.stringify(m.metrics_json || {}, null, 0)}</pre>
            </div>
          ))}
        </div>
      </div>
    </FiscalPageLayout>
  );
}

export function AtRiskLockersPage() {
  const [page, setPage] = useState(1);
  const [hmax, setHmax] = useState(30);
  const [reg, setReg] = useState("");
  const [op, setOp] = useState("");
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const load = () => {
    const q = { page, page_size: 15, health_max: hmax };
    if (reg.trim()) q.region = reg.trim();
    if (op.trim()) q.operator_id = op.trim();
    mlIntelligenceApi
      .atRisk(q)
      .then(setD)
      .catch((e) => setErr(String(e.message || e)));
  };
  useEffect(() => {
    void load();
  }, [page]);
  const csv = () => {
    const rows = d?.rows || [];
    const h = ["locker_id", "health_score", "failure_probability", "battery_min", "door_failures_70d", "last_prediction_at", "region", "operator_id"];
    const lines = [h.join(",")];
    for (const r of rows) lines.push(h.map((k) => `"${String(r[k] ?? "").replace(/"/g, '""')}"`).join(","));
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "at-risk-lockers.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  };
  return (
    <FiscalPageLayout>
      <div style={{ padding: 20, maxWidth: 1100, margin: "0 auto", color: "#e2e8f0" }}>
        <h1 style={{ fontSize: 22 }}>Lockers em risco</h1>
        {err ? <p style={{ color: "#f87171" }}>{err}</p> : null}
        <div style={{ ...G, display: "flex", flexWrap: "wrap", gap: 8, alignItems: "flex-end" }}>
          <label style={{ fontSize: 12 }}>
            health &lt;
            <input type="number" value={hmax} onChange={(e) => setHmax(Number(e.target.value))} style={{ width: 56, marginLeft: 6, background: "#020617", color: "#fff", border: "1px solid #475569", borderRadius: 6 }} />
          </label>
          <input placeholder="region" value={reg} onChange={(e) => setReg(e.target.value)} style={{ padding: 6, background: "#020617", color: "#fff", border: "1px solid #475569", borderRadius: 6 }} />
          <input placeholder="operator_id" value={op} onChange={(e) => setOp(e.target.value)} style={{ padding: 6, background: "#020617", color: "#fff", border: "1px solid #475569", borderRadius: 6 }} />
          <button type="button" onClick={() => { setPage(1); void load(); }} style={{ padding: "8px 12px", background: "#334155", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer" }}>
            Filtrar
          </button>
          <button type="button" onClick={csv} style={{ padding: "8px 12px", background: "#0ea5e9", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer" }}>
            Export CSV
          </button>
        </div>
        <div style={{ ...G, overflow: "auto" }}>
          <table style={TBL}>
            <thead>
              <tr>
                {["locker_id", "health_score", "failure_probability", "battery_min", "door_failures_70d", "last_prediction_at", "region"].map((c) => (
                  <th key={c} style={TH}>
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(d?.rows || []).map((r) => (
                <tr key={`${r.locker_id}-${r.last_prediction_at}`} style={{ transition: "background .15s" }} onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(51,65,85,0.4)")} onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
                  <td style={TD}>{r.locker_id}</td>
                  <td style={TD}>{r.health_score}</td>
                  <td style={TD}>{r.failure_probability != null ? Number(r.failure_probability).toFixed(4) : ""}</td>
                  <td style={TD}>{r.battery_min}</td>
                  <td style={TD}>{r.door_failures_70d}</td>
                  <td style={TD}>{r.last_prediction_at ? String(r.last_prediction_at).slice(0, 19) : ""}</td>
                  <td style={TD}>{r.region}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: 10, display: "flex", gap: 8 }}>
            <button type="button" disabled={page <= 1} onClick={() => setPage((p) => p - 1)} style={{ padding: 6, cursor: page <= 1 ? "not-allowed" : "pointer" }}>
              Anterior
            </button>
            <span style={{ fontSize: 12, color: "#94a3b8" }}>
              Pág {page} / {d?.total != null ? Math.max(1, Math.ceil(d.total / 15)) : "?"}
            </span>
            <button type="button" onClick={() => setPage((p) => p + 1)} style={{ padding: 6, cursor: "pointer" }}>
              Próxima
            </button>
          </div>
        </div>
      </div>
    </FiscalPageLayout>
  );
}

export function PredictionHistoryPage() {
  const [days, setDays] = useState(30);
  const [lid, setLid] = useState("");
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const load = () => {
    const q = { days };
    if (lid.trim()) q.locker_id = lid.trim();
    mlIntelligenceApi
      .history(q)
      .then(setD)
      .catch((e) => setErr(String(e.message || e)));
  };
  useEffect(() => {
    void load();
  }, [days]);
  const chart = (d?.stacked_daily || []).map((x) => ({ ...x, d: String(x.d) }));
  return (
    <FiscalPageLayout>
      <div style={{ padding: 20, maxWidth: 1100, margin: "0 auto", color: "#e2e8f0" }}>
        <h1 style={{ fontSize: 22 }}>Histórico de predições</h1>
        <p style={{ fontSize: 12, color: "#94a3b8" }}>Barras: alinhamento predição vs rótulo (failure_label 70d/7d, mesmo dia).</p>
        {err ? <p style={{ color: "#f87171" }}>{err}</p> : null}
        <div style={{ ...G, display: "flex", gap: 8, flexWrap: "wrap" }}>
          {[7, 30, 90].map((n) => (
            <button key={n} type="button" onClick={() => setDays(n)} style={{ padding: "6px 12px", borderRadius: 8, border: days === n ? "1px solid #34d399" : "1px solid #475569", background: days === n ? "rgba(52,211,153,0.12)" : "#0f172a", color: "#e2e8f0", cursor: "pointer" }}>
              {n}d
            </button>
          ))}
          <input placeholder="locker_id" value={lid} onChange={(e) => setLid(e.target.value)} style={{ padding: 6, flex: 1, minWidth: 160, background: "#020617", color: "#fff", border: "1px solid #475569", borderRadius: 6 }} />
          <button type="button" onClick={() => void load()} style={{ padding: "8px 12px", background: "#334155", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer" }}>
            Aplicar
          </button>
        </div>
        <div style={{ ...G, height: 400 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart}>
              <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
              <XAxis dataKey="d" tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
              <Legend />
              <Bar dataKey="n_correct" name="alinhado" stackId="a" fill="#34d399" />
              <Bar dataKey="n_wrong" name="divergente" stackId="a" fill="#f87171" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div style={{ ...G, overflow: "auto", maxHeight: 360 }}>
          <table style={TBL}>
            <thead>
              <tr>
                {["locker_id", "predicted_at", "failure_probability", "health_score", "model_version"].map((c) => (
                  <th key={c} style={TH}>
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(d?.predictions || []).map((r, i) => (
                <tr key={i}>
                  <td style={TD}>{r.locker_id}</td>
                  <td style={TD}>{r.predicted_at ? String(r.predicted_at).slice(0, 19) : ""}</td>
                  <td style={TD}>{r.failure_probability != null ? Number(r.failure_probability).toFixed(4) : ""}</td>
                  <td style={TD}>{r.health_score}</td>
                  <td style={TD}>{r.model_version}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </FiscalPageLayout>
  );
}

export function PartnerChurnPage() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [thr, setThr] = useState(70);
  useEffect(() => {
    mlIntelligenceApi
      .churnRisk({ min_risk: thr })
      .then(setD)
      .catch((e) => setErr(String(e.message || e)));
  }, [thr]);
  const high = d?.high_risk || [];
  return (
    <FiscalPageLayout>
      <div className="intel-ml-surface" style={{ padding: 20, maxWidth: 960, margin: "0 auto", color: "var(--fiscal-text)" }}>
        <h1 className="intel-ml-pageTitle" style={{ fontSize: 22 }}>
          Churn — parceiros logísticos
        </h1>
        <p className="intel-ml-pageSub" style={{ fontSize: 12, marginBottom: 12 }}>
          risk_score = P(churn)×100. Treino: <span className="intel-ml-code">PYTHONPATH=. python -m app.ml_churn.train_churn_model</span>
        </p>
        <div className="intel-ml-card intel-ml-card--toolbar" style={{ gap: 10, alignItems: "center" }}>
          <label className="intel-ml-field" style={{ fontSize: 13 }}>
            <span className="intel-ml-fieldLabel">Limiar mínimo</span>
            <input
              type="number"
              className="intel-ml-input"
              value={thr}
              min={0}
              max={100}
              onChange={(e) => setThr(Number(e.target.value))}
              style={{ width: 88, marginTop: 4 }}
            />
          </label>
          <button
            type="button"
            className="intel-ml-btn intel-ml-btn--primary"
            onClick={() => mlIntelligenceApi.churnRisk({ min_risk: thr }).then(setD).catch((e) => setErr(String(e.message || e)))}
          >
            Atualizar
          </button>
        </div>
        {err ? <p className="intel-ml-error">{err}</p> : null}
        <Card title={`Parceiros com risk_score ≥ ${thr} (${high.length})`}>
          <table style={TBL}>
            <thead>
              <tr>
                {["partner_id", "name", "code", "active", "risk_score", "churn_probability"].map((c) => (
                  <th key={c} style={TH}>
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {high.map((r) => (
                <tr key={r.partner_id}>
                  <td style={TD}>{r.partner_id}</td>
                  <td style={TD}>{r.name}</td>
                  <td style={TD}>{r.code}</td>
                  <td style={TD}>{r.active ? "sim" : "não"}</td>
                  <td style={TD}>{r.risk_score}</td>
                  <td style={TD}>{r.churn_probability != null ? Number(r.churn_probability).toFixed(4) : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </FiscalPageLayout>
  );
}

export function CustomerLTVScoresPage() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [seg, setSeg] = useState("");
  const [page, setPage] = useState(1);
  const load = () => {
    const q = { page, page_size: 25 };
    if (seg.trim()) q.segment = seg.trim();
    mlIntelligenceApi
      .ltvScores(q)
      .then(setD)
      .catch((e) => setErr(String(e.message || e)));
  };
  useEffect(() => {
    void load();
  }, [page]);
  const rows = d?.rows || [];
  const dist = d?.segment_distribution || [];
  return (
    <FiscalPageLayout>
      <div className="intel-ml-surface" style={{ padding: 20, maxWidth: 1100, margin: "0 auto", color: "var(--fiscal-text)" }}>
        <h1 className="intel-ml-pageTitle" style={{ fontSize: 22 }}>
          LTV preditivo (clientes)
        </h1>
        <p className="intel-ml-pageSub" style={{ fontSize: 12, marginBottom: 12 }}>
          BG/NBD + Gamma-Gamma (lifetimes). Treino:{" "}
          <span className="intel-ml-code">PYTHONPATH=. python -m app.ml_ltv.ltv_model_train --materialize</span> · API:{" "}
          <span className="intel-ml-code">GET /customers/&#123;id&#125;/ltv</span>
        </p>
        <div className="intel-ml-card intel-ml-card--toolbar" style={{ gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <label className="intel-ml-field" style={{ fontSize: 13 }}>
            <span className="intel-ml-fieldLabel">Segmento (exato)</span>
            <input
              className="intel-ml-input"
              placeholder="High Value | Medium Value | Low Value"
              value={seg}
              onChange={(e) => setSeg(e.target.value)}
              style={{ width: 260, marginTop: 4 }}
            />
          </label>
          <button type="button" className="intel-ml-btn intel-ml-btn--primary" onClick={() => { setPage(1); void load(); }}>
            Filtrar
          </button>
          <span style={{ fontSize: 12, color: "var(--fiscal-muted)" }}>
            Total: {d?.total ?? "—"} · Distribuição: {dist.map((x) => `${x.segmento_cliente}=${x.n}`).join(", ") || "—"}
          </span>
        </div>
        {err ? <p className="intel-ml-error">{err}</p> : null}
        <Card title="customer_ltv_scores (materializado)">
          <div style={{ overflow: "auto" }}>
            <table style={TBL}>
              <thead>
                <tr>
                  {[
                    "user_id",
                    "LTV 12m (¢)",
                    "P5–P95 (¢)",
                    "churn_30d",
                    "p_alive",
                    "segmento",
                    "campanha",
                    "notif 90d",
                    "scored_at",
                  ].map((c) => (
                    <th key={c} style={TH}>
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.user_id}>
                    <td style={TD}>{r.user_id}</td>
                    <td style={TD}>{r.predicted_ltv_12m_cents}</td>
                    <td style={TD}>
                      {r.ltv_p05_cents}–{r.ltv_p95_cents}
                    </td>
                    <td style={TD}>{r.churn_probability_30d != null ? Number(r.churn_probability_30d).toFixed(4) : ""}</td>
                    <td style={TD}>{r.p_alive != null ? Number(r.p_alive).toFixed(4) : ""}</td>
                    <td style={TD}>{r.segmento_cliente}</td>
                    <td style={TD} title={r.campaign_segment}>
                      {(r.campaign_segment || "").slice(0, 42)}
                      {(r.campaign_segment || "").length > 42 ? "…" : ""}
                    </td>
                    <td style={TD}>{r.notification_engagement_90d}</td>
                    <td style={TD}>{r.scored_at ? String(r.scored_at).slice(0, 19) : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "center" }}>
            <button type="button" className="intel-ml-btn" disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
              Anterior
            </button>
            <span style={{ fontSize: 12 }}>Página {page}</span>
            <button type="button" className="intel-ml-btn" disabled={!d || rows.length < 25} onClick={() => setPage((p) => p + 1)}>
              Próxima
            </button>
          </div>
        </Card>
      </div>
    </FiscalPageLayout>
  );
}

export function DynamicPricingPage() {
  const [lockerId, setLockerId] = useState("");
  const [productId, setProductId] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const run = () => {
    if (!lockerId.trim() || !productId.trim()) {
      setErr("Informe locker_id e product_id (SKU).");
      return;
    }
    setBusy(true);
    setErr("");
    const body = {
      locker_id: lockerId.trim(),
      product_id: productId.trim(),
      ...(sessionId.trim() ? { session_id: sessionId.trim() } : {}),
    };
    mlIntelligenceApi
      .dynamicPricingSuggest(body)
      .then(setD)
      .catch((e) => setErr(String(e.message || e)))
      .finally(() => setBusy(false));
  };
  const shap = d?.explainability?.linear_shap?.feature_values;
  return (
    <FiscalPageLayout>
      <div className="intel-ml-surface" style={{ padding: 20, maxWidth: 960, margin: "0 auto", color: "var(--fiscal-text)" }}>
        <h1 className="intel-ml-pageTitle" style={{ fontSize: 22 }}>
          Preços dinâmicos
        </h1>
        <p className="intel-ml-pageSub" style={{ fontSize: 12, marginBottom: 12 }}>
          Bandit contextual (Thompson) + elasticidade histórica. POST <span className="intel-ml-code">/pricing/dynamic-suggest</span>
        </p>
        <div className="intel-ml-card intel-ml-card--toolbar" style={{ flexWrap: "wrap", gap: 10, alignItems: "flex-end" }}>
          <label className="intel-ml-field" style={{ fontSize: 13, flex: "1 1 140px" }}>
            <span className="intel-ml-fieldLabel">locker_id</span>
            <input className="intel-ml-input" value={lockerId} onChange={(e) => setLockerId(e.target.value)} style={{ display: "block", width: "100%", marginTop: 4 }} />
          </label>
          <label className="intel-ml-field" style={{ fontSize: 13, flex: "1 1 140px" }}>
            <span className="intel-ml-fieldLabel">product_id (SKU)</span>
            <input className="intel-ml-input" value={productId} onChange={(e) => setProductId(e.target.value)} style={{ display: "block", width: "100%", marginTop: 4 }} />
          </label>
          <label className="intel-ml-field" style={{ fontSize: 13, flex: "1 1 160px" }}>
            <span className="intel-ml-fieldLabel">session_id (A/B, opcional)</span>
            <input className="intel-ml-input" value={sessionId} onChange={(e) => setSessionId(e.target.value)} style={{ display: "block", width: "100%", marginTop: 4 }} />
          </label>
          <button type="button" disabled={busy} className="intel-ml-btn intel-ml-btn--primary" onClick={run}>
            {busy ? "…" : "Sugerir preço"}
          </button>
        </div>
        {err ? <p className="intel-ml-error" style={{ marginTop: 12 }}>{err}</p> : null}
        {d ? (
          <>
            <div style={{ ...G, marginTop: 16 }}>
              <p style={{ margin: "0 0 8px", fontSize: 13 }}>
                Variante A/B: <strong>{d.ab_variant}</strong>
                {d.ab_note ? <span style={{ color: "var(--fiscal-muted)" }}> — {d.ab_note}</span> : null}
              </p>
              <p style={{ margin: 0, fontSize: 14 }}>
                Ajuste sugerido: <strong>{d.suggested_price_adjust_pct}%</strong> · multiplicador {d.suggested_price_multiplier} ·{" "}
                <strong>{d.suggested_unit_amount_cents}</strong> centavos (base {d.context?.base_price_cents})
              </p>
              <p style={{ margin: "8px 0 0", fontSize: 13, color: "var(--fiscal-muted)" }}>
                Desconto estoque: {d.recommended_discount_pct_clear_stock}% · braço {d.arm_index} · proxy receita {d.revenue_proxy_cents}
              </p>
            </div>
            {d.bundle_recommendation ? (
              <Card title="Bundle sugerido">
                <p style={{ margin: 0, fontSize: 13 }}>
                  {d.bundle_recommendation.name} ({d.bundle_recommendation.code}) — {d.bundle_recommendation.amount_cents}{" "}
                  {d.bundle_recommendation.currency}
                </p>
              </Card>
            ) : null}
            {shap ? (
              <Card title="Explainability (SHAP linear no score do braço)">
                <table style={TBL}>
                  <thead>
                    <tr>
                      <th style={TH}>feature</th>
                      <th style={TH}>contribuição</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(shap).map(([k, v]) => (
                      <tr key={k}>
                        <td style={TD}>{k}</td>
                        <td style={TD}>{typeof v === "number" ? v.toFixed(4) : String(v)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            ) : null}
          </>
        ) : null}
      </div>
    </FiscalPageLayout>
  );
}

export function PickupFraudDashboardPage() {
  const [days, setDays] = useState(30);
  const [hot, setHot] = useState(null);
  const [pickupId, setPickupId] = useState("");
  const [score, setScore] = useState(null);
  const [postRes, setPostRes] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    mlIntelligenceApi
      .pickupFraudHotspots(days)
      .then(setHot)
      .catch((e) => setErr(String(e.message || e)));
  }, [days]);
  const runScore = () => {
    const id = pickupId.trim();
    if (!id) {
      setErr("Informe pickup_id.");
      return;
    }
    setErr("");
    mlIntelligenceApi
      .pickupFraudScore(id)
      .then(setScore)
      .catch((e) => setErr(String(e.message || e)));
  };
  const runPost = () => {
    const id = pickupId.trim();
    if (!id) {
      setErr("Informe pickup_id.");
      return;
    }
    setErr("");
    mlIntelligenceApi
      .pickupFraudCheckPost(id, { apply_block: true })
      .then(setPostRes)
      .catch((e) => setErr(String(e.message || e)));
  };
  const rows = hot?.lockers || [];
  return (
    <FiscalPageLayout>
      <div className="intel-ml-surface" style={{ padding: 20, maxWidth: 960, margin: "0 auto", color: "var(--fiscal-text)" }}>
        <h1 className="intel-ml-pageTitle" style={{ fontSize: 22 }}>
          Fraude / anomalia em pickups
        </h1>
        <p className="intel-ml-pageSub" style={{ fontSize: 12, marginBottom: 12 }}>
          Isolation Forest + Autoencoder · score ≥0.9 marca <span className="intel-ml-code">fraud_flag</span> +{" "}
          <span className="intel-ml-code">audit_logs</span>. Hotspots por locker na janela.
        </p>
        <div className="intel-ml-card intel-ml-card--toolbar" style={{ flexWrap: "wrap", gap: 10, alignItems: "flex-end" }}>
          <label className="intel-ml-field">
            <span className="intel-ml-fieldLabel">Janela (dias)</span>
            <select className="intel-ml-select" value={days} onChange={(e) => setDays(Number(e.target.value))}>
              {[7, 14, 30, 60, 90].map((d) => (
                <option key={d} value={d}>
                  {d}d
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="intel-ml-btn intel-ml-btn--primary"
            onClick={() =>
              mlIntelligenceApi
                .pickupFraudHotspots(days)
                .then(setHot)
                .catch((e) => setErr(String(e.message || e)))
            }
          >
            Atualizar hotspots
          </button>
        </div>
        <Card title={`Lockers com mais fraud_flag na janela (${days}d) — ${rows.length} lockers`}>
          <table style={TBL}>
            <thead>
              <tr>
                <th style={TH}>locker_id</th>
                <th style={TH}>fraud_pickups</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.locker_id}>
                  <td style={TD}>{r.locker_id}</td>
                  <td style={TD}>{r.fraud_pickups}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
        <div className="intel-ml-card intel-ml-card--toolbar" style={{ marginTop: 16, flexWrap: "wrap", gap: 10 }}>
          <label className="intel-ml-field" style={{ flex: "1 1 220px" }}>
            <span className="intel-ml-fieldLabel">pickup_id (score em tempo real)</span>
            <input className="intel-ml-input" value={pickupId} onChange={(e) => setPickupId(e.target.value)} style={{ width: "100%", marginTop: 4 }} />
          </label>
          <button type="button" className="intel-ml-btn" onClick={runScore}>
            Score (sem bloquear)
          </button>
          <button type="button" className="intel-ml-btn intel-ml-btn--primary" onClick={runPost}>
            POST fraud-check (bloquear se ≥0.9)
          </button>
        </div>
        {err ? <p className="intel-ml-error">{err}</p> : null}
        {score ? (
          <Card title="Score (somente leitura)">
            <pre style={{ ...TD, fontSize: 11, overflow: "auto", background: "var(--fiscal-code-bg)", padding: 12, borderRadius: 8 }}>
              {JSON.stringify(score, null, 2)}
            </pre>
          </Card>
        ) : null}
        {postRes ? (
          <Card title="Resposta POST /pickups/…/fraud-check">
            <pre style={{ ...TD, fontSize: 11, overflow: "auto", background: "var(--fiscal-code-bg)", padding: 12, borderRadius: 8 }}>
              {JSON.stringify(postRes, null, 2)}
            </pre>
          </Card>
        ) : null}
      </div>
    </FiscalPageLayout>
  );
}

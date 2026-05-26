import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import {
  apiKeyBannerStyle,
  buttonGhostStyle,
  buttonPrimaryStyle,
  cardStyle,
  criticalBannerStyle,
  crossShortcutLinkStyle,
  healthLocalFilterInputStyle,
  mutedTextStyle,
  okBannerStyle,
  opsSanityCardStyle,
  pageStyle,
  summary24hHeaderStyle,
  summary24hHintStyle,
  tabButtonStyle,
  tableStyle,
  tdStyle,
  thStyle,
  toolbarStyle,
} from "../styles/opsShellStyles";

const BASE = import.meta.env.VITE_ANALYTICS_BI_ADMIN_BASE_URL || "/api/bia";
const API = `${BASE}/v1/analytics-bi-admin`;
const PAGE_VERSION = "ops/bi-analytics/admin v0.2";

const TAB_ITEMS = [
  { id: "overview", label: "Visao geral", group: "Hub" },
  { id: "intelligence", label: "Ops intelligence", group: "Hub" },
  { id: "readiness", label: "Prontidao", group: "Hub" },
  { id: "efficiency", label: "Eficiencia", group: "Hub" },
  { id: "facts", label: "Facts", group: "Dados" },
  { id: "marts", label: "Marts", group: "Dados" },
  { id: "refresh", label: "Refresh ETL", group: "Dados" },
  { id: "lineage", label: "Lineage", group: "Dados" },
  { id: "exports", label: "Exports", group: "Dados" },
  { id: "kpis", label: "KPIs", group: "Monitoramento" },
  { id: "alerts", label: "Alertas", group: "Monitoramento" },
  { id: "reports", label: "Relatorios", group: "Monitoramento" },
  { id: "players", label: "Players mundial", group: "Ecossistema" },
  { id: "taxonomy", label: "Taxonomia", group: "Ecossistema" },
  { id: "partners", label: "Parceiros BI", group: "Integracao" },
  { id: "webhooks", label: "Webhooks", group: "Integracao" },
  { id: "integration", label: "Hub dominios", group: "Integracao" },
  { id: "audit", label: "Auditoria", group: "Governanca" },
];

const OVERVIEW_KPIS = [
  ["facts_count", "Facts totais"],
  ["facts_24h", "Facts 24h"],
  ["partners", "Parceiros BI"],
  ["kpi_definitions", "Definicoes KPI"],
  ["report_catalog", "Relatorios"],
  ["network_players", "Players rede"],
  ["mrr_rows", "Linhas MRR"],
  ["locker_pnl_rows", "Linhas P&L"],
  ["readiness_go_live", "GO_LIVE"],
  ["readiness_avg_score", "Score readiness"],
  ["open_kpi_alerts", "Alertas abertos"],
  ["lineage_edges", "Lineage"],
  ["market_presence_rows", "Presenca mercado"],
  ["export_jobs_24h", "Exports 24h"],
];

function parseError(payload, fallback = "Falha na API BI admin.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  return fallback;
}

function normalizeNetworkError(err) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao. Verifique proxy ${BASE} (porta 8026) e ./dev.sh no analytics-bi-admin.`;
  }
  return raw;
}

function JsonBlock({ data, maxHeight = 360 }) {
  if (!data) return <p style={mutedTextStyle}>Sem dados.</p>;
  return (
    <pre style={{ ...cardStyle, maxHeight, overflow: "auto", fontSize: 11, margin: 0 }}>
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

function DataTable({ columns, rows, empty = "Nenhum registro." }) {
  if (!rows?.length) return <p style={mutedTextStyle}>{empty}</p>;
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={tableStyle}>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} style={thStyle}>
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.id || row.code || i}>
              {columns.map((c) => (
                <td key={c.key} style={tdStyle}>
                  {c.render ? c.render(row) : String(row[c.key] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function OpsBiAnalyticsAdminPage() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get("tab") || "overview";
  const [tab, setTab] = useState(TAB_ITEMS.some((t) => t.id === initialTab) ? initialTab : "overview");

  const [dash, setDash] = useState(null);
  const [opsIntel, setOpsIntel] = useState(null);
  const [readiness, setReadiness] = useState({ rows: [], bands: {}, avg_score: 0 });
  const [facts, setFacts] = useState([]);
  const [marts, setMarts] = useState(null);
  const [martJobs, setMartJobs] = useState([]);
  const [kpis, setKpis] = useState([]);
  const [alertRules, setAlertRules] = useState([]);
  const [alertEvents, setAlertEvents] = useState([]);
  const [lineage, setLineage] = useState([]);
  const [exportJobs, setExportJobs] = useState([]);
  const [reports, setReports] = useState([]);
  const [partners, setPartners] = useState([]);
  const [players, setPlayers] = useState([]);
  const [relations, setRelations] = useState([]);
  const [taxonomy, setTaxonomy] = useState([]);
  const [marketPresence, setMarketPresence] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [audit, setAudit] = useState([]);
  const [integrationLinks, setIntegrationLinks] = useState(null);
  const [domainLinks, setDomainLinks] = useState([]);
  const [tier1Coverage, setTier1Coverage] = useState(null);
  const [efficiency, setEfficiency] = useState(null);
  const [dqChecks, setDqChecks] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [bookmarks, setBookmarks] = useState([]);
  const [pipelines, setPipelines] = useState([]);

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const [rotatedKey, setRotatedKey] = useState("");

  const [partnerForm, setPartnerForm] = useState({ name: "", code: "", partner_type: "WAREHOUSE" });
  const [factForm, setFactForm] = useState({
    fact_key: "",
    fact_name: "",
    order_id: "",
    payload: '{"event":"demo"}',
  });
  const [webhookForm, setWebhookForm] = useState({
    network_player_code: "INPOST",
    capability_code: "MART_REFRESH",
    url: "",
    secret: "",
  });
  const [playerFilter, setPlayerFilter] = useState("");

  const headers = useMemo(
    () => ({
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }),
    [token],
  );

  const apiFetch = useCallback(
    async (path, options = {}) => {
      const res = await fetch(`${API}${path}`, {
        ...options,
        headers: { ...headers, ...(options.headers || {}) },
      });
      const text = await res.text();
      let body = null;
      try {
        body = text ? JSON.parse(text) : null;
      } catch {
        body = text;
      }
      if (!res.ok) throw new Error(parseError(body, `HTTP ${res.status}`));
      return body;
    },
    [headers],
  );

  const setTabAndUrl = (id) => {
    setTab(id);
    if (id === "overview") setSearchParams({}, { replace: true });
    else setSearchParams({ tab: id }, { replace: true });
  };

  useEffect(() => {
    const q = searchParams.get("tab");
    if (!q && tab !== "overview") setTab("overview");
    if (q && TAB_ITEMS.some((t) => t.id === q) && q !== tab) setTab(q);
  }, [searchParams, tab]);

  const loadEfficiency = useCallback(async () => {
    const [sc, dq, an, bm, pl] = await Promise.all([
      apiFetch("/efficiency/scorecard"),
      apiFetch("/efficiency/data-quality-checks"),
      apiFetch("/efficiency/anomaly-signals?status=OPEN"),
      apiFetch("/efficiency/bookmarks"),
      apiFetch("/efficiency/pipeline-sync"),
    ]);
    setEfficiency(sc);
    setDqChecks(dq.checks || []);
    setAnomalies(an.signals || []);
    setBookmarks(bm.bookmarks || []);
    setPipelines(Array.isArray(pl) ? pl : []);
  }, [apiFetch]);

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    setOk("");
    try {
      const d = await apiFetch("/dashboard");
      setDash(d);

      const tasks = [];
      if (tab === "intelligence") tasks.push(apiFetch("/ops-intelligence/summary").then(setOpsIntel));
      if (tab === "readiness") {
        tasks.push(
          apiFetch("/data-readiness").then((r) =>
            setReadiness({ rows: r.rows || [], bands: r.bands || {}, avg_score: r.avg_score || 0 }),
          ),
        );
      }
      if (tab === "facts") tasks.push(apiFetch("/analytics-facts?limit=50").then((r) => setFacts(r.items || [])));
      if (tab === "marts") tasks.push(apiFetch("/marts").then(setMarts));
      if (tab === "refresh") tasks.push(apiFetch("/mart-refresh-jobs").then((r) => setMartJobs(r.jobs || [])));
      if (tab === "kpis") tasks.push(apiFetch("/kpi-definitions").then((r) => setKpis(r.items || [])));
      if (tab === "alerts") {
        tasks.push(
          Promise.all([apiFetch("/kpi-alert-rules"), apiFetch("/kpi-alert-events?status=OPEN")]).then(
            ([rules, events]) => {
              setAlertRules(rules.rules || []);
              setAlertEvents(events.events || []);
            },
          ),
        );
      }
      if (tab === "lineage") tasks.push(apiFetch("/data-lineage").then((r) => setLineage(r.edges || [])));
      if (tab === "exports") tasks.push(apiFetch("/export-jobs").then((r) => setExportJobs(r.jobs || [])));
      if (tab === "reports") tasks.push(apiFetch("/report-catalog").then((r) => setReports(r.items || [])));
      if (tab === "partners") tasks.push(apiFetch("/bi-data-partners").then((r) => setPartners(r.partners || [])));
      if (tab === "players") {
        tasks.push(
          Promise.all([
            apiFetch("/bi-locker-network-players"),
            apiFetch("/bi-locker-network-players/relations"),
            apiFetch("/bi-locker-network-players/tier1-coverage"),
          ]).then(([pl, rel, t1]) => {
            setPlayers(pl.players || []);
            setRelations(rel.relations || []);
            setTier1Coverage(t1);
          }),
        );
      }
      if (tab === "taxonomy") {
        tasks.push(
          Promise.all([
            apiFetch("/player-segment-taxonomy"),
            apiFetch("/player-market-presence"),
          ]).then(([seg, pres]) => {
            setTaxonomy(seg.segments || []);
            setMarketPresence(pres.presence || []);
          }),
        );
      }
      if (tab === "webhooks") tasks.push(apiFetch("/bi-capability-webhooks").then((r) => setWebhooks(r.webhooks || [])));
      if (tab === "audit") tasks.push(apiFetch("/ops-audit-log").then((r) => setAudit(r.events || [])));
      if (tab === "integration") {
        tasks.push(
          Promise.all([apiFetch("/integration-hub/links"), apiFetch("/unified-domain-links")]).then(
            ([links, domains]) => {
              setIntegrationLinks(links);
              setDomainLinks(domains.links || []);
            },
          ),
        );
      }
      if (tab === "efficiency") tasks.push(loadEfficiency());

      await Promise.all(tasks);
    } catch (e) {
      setErr(normalizeNetworkError(e));
    } finally {
      setLoading(false);
    }
  }, [apiFetch, tab, loadEfficiency]);

  useEffect(() => {
    void load();
  }, [load]);

  const onSeed = async () => {
    try {
      await apiFetch("/seed", { method: "POST" });
      await apiFetch("/ops-intelligence/seed-professional", { method: "POST" });
      setOk("Seed BI/Analytics concluido.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e));
    }
  };

  const onRecomputeReadiness = async () => {
    try {
      await apiFetch("/data-readiness/recompute", { method: "POST" });
      setOk("Readiness recomputado.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e));
    }
  };

  const onSeedPlayers = async () => {
    try {
      await apiFetch("/bi-locker-network-players/seed-global-catalog", { method: "POST" });
      setOk("Catalogo global de players atualizado.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e));
    }
  };

  const onRefreshMart = async () => {
    try {
      await apiFetch("/mart-refresh-jobs", {
        method: "POST",
        body: JSON.stringify({ mart_name: "locker_pnl", triggered_by: "ops-ui-v0" }),
      });
      setOk("Job de refresh locker_pnl disparado.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e));
    }
  };

  const onExport = async () => {
    try {
      await apiFetch("/export-jobs", {
        method: "POST",
        body: JSON.stringify({ dataset_code: "PARTNER_REVENUE_MONTHLY" }),
      });
      setOk("Export job enfileirado.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e));
    }
  };

  const onRotate = async (partnerId) => {
    try {
      const r = await apiFetch(`/bi-data-partners/${partnerId}/api-keys/rotate`, { method: "POST" });
      setRotatedKey(r.api_key || "");
      setOk("API key rotacionada.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e));
    }
  };

  const onCreatePartner = async (e) => {
    e.preventDefault();
    try {
      await apiFetch("/bi-data-partners", {
        method: "POST",
        body: JSON.stringify({
          id: `bi-${partnerForm.code.toLowerCase()}`,
          name: partnerForm.name,
          code: partnerForm.code,
          partner_type: partnerForm.partner_type,
        }),
      });
      setPartnerForm({ name: "", code: "", partner_type: "WAREHOUSE" });
      setOk("Parceiro BI criado.");
      await load();
    } catch (ex) {
      setErr(normalizeNetworkError(ex));
    }
  };

  const onCreateFact = async (e) => {
    e.preventDefault();
    let payload = {};
    try {
      payload = JSON.parse(factForm.payload || "{}");
    } catch {
      setErr("Payload JSON invalido.");
      return;
    }
    try {
      await apiFetch("/analytics-facts", {
        method: "POST",
        body: JSON.stringify({
          fact_key: factForm.fact_key,
          fact_name: factForm.fact_name,
          order_id: factForm.order_id,
          payload,
          occurred_at: new Date().toISOString(),
        }),
      });
      setFactForm({ fact_key: "", fact_name: "", order_id: "", payload: '{"event":"demo"}' });
      setOk("Fact inserido.");
      await load();
    } catch (ex) {
      setErr(normalizeNetworkError(ex));
    }
  };

  const onCreateWebhook = async (e) => {
    e.preventDefault();
    try {
      await apiFetch("/bi-capability-webhooks", {
        method: "POST",
        body: JSON.stringify(webhookForm),
      });
      setWebhookForm({ ...webhookForm, url: "", secret: "" });
      setOk("Webhook registrado.");
      await load();
    } catch (ex) {
      setErr(normalizeNetworkError(ex));
    }
  };

  const filteredPlayers = useMemo(() => {
    const q = playerFilter.trim().toLowerCase();
    if (!q) return players;
    return players.filter(
      (p) =>
        String(p.code || "").toLowerCase().includes(q) ||
        String(p.name || "").toLowerCase().includes(q) ||
        String(p.country || "").toLowerCase().includes(q),
    );
  }, [players, playerFilter]);

  const tabGroups = useMemo(() => {
    const map = new Map();
    TAB_ITEMS.forEach((t) => {
      if (!map.has(t.group)) map.set(t.group, []);
      map.get(t.group).push(t);
    });
    return [...map.entries()];
  }, []);

  const listTitle =
    tab === "overview"
      ? "Indicadores do dashboard BI"
      : TAB_ITEMS.find((t) => t.id === tab)?.label || tab;

  return (
    <div style={pageStyle} data-testid="ops-bi-analytics-admin-page">
      <section style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10, gap: 8 }}>
          <Link to="/ops/ml/admin" style={crossShortcutLinkStyle}>
            ML OPS
          </Link>
          <Link to="/ops/analytics/financial" style={crossShortcutLinkStyle}>
            Analytics financeiro
          </Link>
          <Link to="/ops/marketplace/admin" style={crossShortcutLinkStyle}>
            Marketplace
          </Link>
          <Link to="/ops/hardware/admin" style={crossShortcutLinkStyle}>
            Hardware
          </Link>
          <Link to="/intelligence/dashboard" style={crossShortcutLinkStyle}>
            Inteligencia preditiva
          </Link>
        </div>

        <OpsPageTitleHeader
          title="BI · Analytics · Machine Learning"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Facts, marts financeiros, KPIs, readiness, ecossistema locker mundial (InPost, DHL, Magalu, Mercado Livre,
          Amazon, DPD, Correios, CTT, Worten, El Corte Ingles) — API{" "}
          <code style={{ color: "#e2e8f0" }}>{API}</code>
        </p>

        <div style={toolbarStyle}>
          <button type="button" style={buttonGhostStyle} onClick={() => void onSeed()} disabled={loading}>
            Seed
          </button>
          <button type="button" style={buttonGhostStyle} onClick={() => void load()} disabled={loading}>
            {loading ? "Carregando…" : "Atualizar"}
          </button>
        </div>

        {err ? <div style={{ ...criticalBannerStyle, marginTop: 10 }}>{err}</div> : null}
        {ok ? <p style={okBannerStyle}>{ok}</p> : null}
        {rotatedKey ? <p style={apiKeyBannerStyle}>Nova API key: {rotatedKey}</p> : null}

        <section style={{ ...opsSanityCardStyle, marginTop: 12 }}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>{listTitle}</h3>
          </div>
          {tabGroups.map(([group, items]) => (
            <div key={group} style={{ marginTop: 8 }}>
              <p style={{ ...summary24hHintStyle, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                {group}
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {items.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    style={tabButtonStyle(tab === t.id)}
                    onClick={() => setTabAndUrl(t.id)}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
          ))}

          {tab === "overview" && dash ? (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))",
                gap: 10,
                marginTop: 14,
              }}
            >
              {OVERVIEW_KPIS.map(([key, label]) => (
                <div key={key} style={{ ...cardStyle, padding: 12 }}>
                  <p style={{ ...mutedTextStyle, marginTop: 0, fontSize: 11 }}>{label}</p>
                  <strong style={{ fontSize: 22 }}>{String(dash[key] ?? "—")}</strong>
                </div>
              ))}
            </div>
          ) : null}

          {tab === "intelligence" && opsIntel ? (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
                gap: 8,
                marginTop: 14,
              }}
            >
              {Object.entries(opsIntel).map(([k, v]) => (
                <div key={k} style={{ ...cardStyle, padding: 10 }}>
                  <p style={{ ...mutedTextStyle, marginTop: 0, fontSize: 10 }}>{k}</p>
                  <strong>{String(v)}</strong>
                </div>
              ))}
            </div>
          ) : null}

          {tab === "readiness" ? (
            <div style={{ marginTop: 14 }}>
              <div style={{ ...toolbarStyle, marginBottom: 10 }}>
                <button type="button" style={buttonGhostStyle} onClick={() => void onRecomputeReadiness()}>
                  Recomputar readiness
                </button>
                <span style={summary24hHintStyle}>
                  Media {readiness.avg_score} · bands {JSON.stringify(readiness.bands)}
                </span>
              </div>
              <div style={cardStyle}>
                <DataTable
                  columns={[
                    { key: "network_player_code", label: "Player" },
                    { key: "readiness_band", label: "Band" },
                    { key: "score_total", label: "Score" },
                    {
                      key: "blockers",
                      label: "Blockers",
                      render: (r) => (Array.isArray(r.blockers) ? r.blockers.join(", ") : "—"),
                    },
                  ]}
                  rows={readiness.rows}
                  empty="Sem snapshots de readiness — rode Seed ou Recomputar."
                />
              </div>
            </div>
          ) : null}

          {tab === "efficiency" ? (
            <div style={{ marginTop: 14 }}>
              <div style={{ ...cardStyle, display: "flex", flexWrap: "wrap", alignItems: "center", gap: 12 }}>
                <span style={{ fontSize: 28, fontWeight: 800, color: "#93c5fd" }}>
                  {efficiency?.efficiency_score ?? "—"}
                </span>
                <span style={summary24hHintStyle}>efficiency score</span>
                <button
                  type="button"
                  style={buttonGhostStyle}
                  onClick={async () => {
                    await apiFetch("/efficiency/data-quality-checks/run", { method: "POST" });
                    await loadEfficiency();
                    setOk("DQ checks executados.");
                  }}
                >
                  Run DQ
                </button>
                <button
                  type="button"
                  style={buttonGhostStyle}
                  onClick={async () => {
                    await apiFetch("/efficiency/anomaly-signals/scan", { method: "POST" });
                    await loadEfficiency();
                    setOk("Scan de anomalias concluido.");
                  }}
                >
                  Scan anomalias
                </button>
                <button
                  type="button"
                  style={buttonGhostStyle}
                  onClick={async () => {
                    await apiFetch("/efficiency/scheduled-exports/tick", { method: "POST" });
                    await loadEfficiency();
                    setOk("Exports agendados processados.");
                  }}
                >
                  Tick exports
                </button>
                <button type="button" style={buttonGhostStyle} onClick={() => void loadEfficiency()}>
                  Atualizar
                </button>
              </div>
              {efficiency?.recommendations?.length ? (
                <ul style={{ ...cardStyle, marginTop: 10, paddingLeft: 20 }}>
                  {efficiency.recommendations.map((r, i) => (
                    <li key={i} style={{ marginBottom: 6, color: "#e2e8f0" }}>
                      {r}
                    </li>
                  ))}
                </ul>
              ) : null}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 10 }}>
                <div style={cardStyle}>
                  <h4 style={{ margin: "0 0 8px" }}>Data quality ({dqChecks.length})</h4>
                  <DataTable
                    columns={[
                      { key: "check_code", label: "Check" },
                      { key: "last_status", label: "Status" },
                      { key: "last_score", label: "Score" },
                    ]}
                    rows={dqChecks}
                  />
                </div>
                <div style={cardStyle}>
                  <h4 style={{ margin: "0 0 8px" }}>Anomalias ({anomalies.length})</h4>
                  <DataTable
                    columns={[
                      { key: "signal_type", label: "Tipo" },
                      { key: "severity", label: "Sev." },
                      { key: "summary", label: "Resumo" },
                    ]}
                    rows={anomalies}
                  />
                </div>
                <div style={cardStyle}>
                  <h4 style={{ margin: "0 0 8px" }}>Bookmarks</h4>
                  <DataTable
                    columns={[
                      { key: "label", label: "Label" },
                      {
                        key: "route_path",
                        label: "Rota",
                        render: (r) => (
                          <Link to={`${r.route_path}?tab=${r.query?.tab || "overview"}`} style={{ color: "#93c5fd" }}>
                            {r.route_path}
                          </Link>
                        ),
                      },
                    ]}
                    rows={bookmarks}
                  />
                </div>
                <div style={cardStyle}>
                  <h4 style={{ margin: "0 0 8px" }}>Pipeline BI → ML</h4>
                  <DataTable
                    columns={[
                      { key: "pipeline_code", label: "Pipeline" },
                      { key: "status", label: "Status" },
                      { key: "lag_minutes", label: "Lag (min)" },
                    ]}
                    rows={pipelines}
                  />
                </div>
              </div>
            </div>
          ) : null}

          {tab === "facts" ? (
            <div style={{ marginTop: 14 }}>
              <form
                onSubmit={(e) => void onCreateFact(e)}
                style={{ ...cardStyle, display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))" }}
              >
                <input
                  style={healthLocalFilterInputStyle}
                  placeholder="fact_key"
                  value={factForm.fact_key}
                  onChange={(e) => setFactForm({ ...factForm, fact_key: e.target.value })}
                  required
                />
                <input
                  style={healthLocalFilterInputStyle}
                  placeholder="fact_name"
                  value={factForm.fact_name}
                  onChange={(e) => setFactForm({ ...factForm, fact_name: e.target.value })}
                  required
                />
                <input
                  style={healthLocalFilterInputStyle}
                  placeholder="order_id"
                  value={factForm.order_id}
                  onChange={(e) => setFactForm({ ...factForm, order_id: e.target.value })}
                  required
                />
                <button type="submit" style={buttonPrimaryStyle}>
                  Inserir fact
                </button>
              </form>
              <div style={{ ...cardStyle, marginTop: 10 }}>
                <DataTable
                  columns={[
                    { key: "fact_key", label: "Key" },
                    { key: "fact_name", label: "Nome" },
                    { key: "order_id", label: "Pedido" },
                    { key: "occurred_at", label: "Quando" },
                  ]}
                  rows={facts}
                />
              </div>
            </div>
          ) : null}

          {tab === "marts" && marts ? (
            <div style={{ ...cardStyle, marginTop: 14, display: "grid", gap: 12 }}>
              <section>
                <h4 style={{ color: "#93c5fd", margin: "0 0 6px" }}>company_mrr_trend</h4>
                <JsonBlock data={marts.mrr} maxHeight={160} />
              </section>
              <section>
                <h4 style={{ color: "#93c5fd", margin: "0 0 6px" }}>locker_pnl</h4>
                <JsonBlock data={marts.locker_pnl} maxHeight={160} />
              </section>
              <section>
                <h4 style={{ color: "#93c5fd", margin: "0 0 6px" }}>partner_revenue_monthly</h4>
                <JsonBlock data={marts.partner_revenue} maxHeight={160} />
              </section>
            </div>
          ) : null}

          {tab === "refresh" ? (
            <div style={{ marginTop: 14 }}>
              <button type="button" style={{ ...buttonPrimaryStyle, marginBottom: 10 }} onClick={() => void onRefreshMart()}>
                Disparar refresh locker_pnl
              </button>
              <div style={cardStyle}>
                <DataTable
                  columns={[
                    { key: "mart_name", label: "Mart" },
                    { key: "status", label: "Status" },
                    { key: "triggered_by", label: "Por" },
                  ]}
                  rows={martJobs}
                />
              </div>
            </div>
          ) : null}

          {tab === "kpis" ? (
            <div style={{ ...cardStyle, marginTop: 14 }}>
              <DataTable
                columns={[
                  { key: "code", label: "Codigo" },
                  { key: "name", label: "Nome" },
                  { key: "domain", label: "Dominio" },
                  { key: "grain", label: "Grain" },
                ]}
                rows={kpis}
              />
            </div>
          ) : null}

          {tab === "alerts" ? (
            <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
              <div style={cardStyle}>
                <h4 style={{ margin: "0 0 8px", color: "#fcd34d" }}>Regras ({alertRules.length})</h4>
                <JsonBlock data={alertRules} maxHeight={200} />
              </div>
              <div style={cardStyle}>
                <h4 style={{ margin: "0 0 8px", color: "#fca5a5" }}>Eventos abertos ({alertEvents.length})</h4>
                <DataTable
                  columns={[
                    { key: "kpi_code", label: "KPI" },
                    { key: "observed_value", label: "Valor" },
                    { key: "status", label: "Status" },
                  ]}
                  rows={alertEvents}
                />
              </div>
            </div>
          ) : null}

          {tab === "reports" ? (
            <div style={{ ...cardStyle, marginTop: 14 }}>
              <DataTable
                columns={[
                  { key: "code", label: "Codigo" },
                  { key: "name", label: "Nome" },
                  { key: "report_type", label: "Tipo" },
                ]}
                rows={reports}
              />
            </div>
          ) : null}

          {tab === "lineage" ? (
            <div style={{ ...cardStyle, marginTop: 14 }}>
              <DataTable
                columns={[
                  { key: "source_object", label: "Origem" },
                  { key: "target_object", label: "Destino" },
                  { key: "transform_type", label: "Transform" },
                ]}
                rows={lineage}
              />
            </div>
          ) : null}

          {tab === "exports" ? (
            <div style={{ marginTop: 14 }}>
              <button type="button" style={{ ...buttonPrimaryStyle, marginBottom: 10 }} onClick={() => void onExport()}>
                Novo export PARTNER_REVENUE_MONTHLY
              </button>
              <div style={cardStyle}>
                <DataTable
                  columns={[
                    { key: "dataset_code", label: "Dataset" },
                    { key: "status", label: "Status" },
                    { key: "row_count", label: "Linhas" },
                  ]}
                  rows={exportJobs}
                />
              </div>
            </div>
          ) : null}

          {tab === "partners" ? (
            <div style={{ marginTop: 14 }}>
              <form
                onSubmit={(e) => void onCreatePartner(e)}
                style={{ ...cardStyle, display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 10 }}
              >
                <input
                  style={healthLocalFilterInputStyle}
                  placeholder="Nome"
                  value={partnerForm.name}
                  onChange={(e) => setPartnerForm({ ...partnerForm, name: e.target.value })}
                  required
                />
                <input
                  style={healthLocalFilterInputStyle}
                  placeholder="Codigo"
                  value={partnerForm.code}
                  onChange={(e) => setPartnerForm({ ...partnerForm, code: e.target.value })}
                  required
                />
                <button type="submit" style={buttonPrimaryStyle}>
                  Criar parceiro
                </button>
              </form>
              <div style={cardStyle}>
                <DataTable
                  columns={[
                    { key: "code", label: "Codigo" },
                    { key: "name", label: "Nome" },
                    { key: "partner_type", label: "Tipo" },
                    {
                      key: "id",
                      label: "API key",
                      render: (p) => (
                        <button type="button" style={buttonGhostStyle} onClick={() => void onRotate(p.id)}>
                          Rotacionar
                        </button>
                      ),
                    },
                  ]}
                  rows={partners}
                />
              </div>
            </div>
          ) : null}

          {tab === "players" ? (
            <div style={{ marginTop: 14 }}>
              {tier1Coverage ? (
                <div style={{ ...cardStyle, marginBottom: 10, borderColor: "rgba(52,211,153,0.45)" }}>
                  <strong style={{ color: "#6ee7b7" }}>
                    Tier-1: {tier1Coverage.tier1_present}/{tier1Coverage.tier1_required} (
                    {tier1Coverage.coverage_pct}%)
                  </strong>
                  <p style={{ ...mutedTextStyle, fontSize: 11 }}>{(tier1Coverage.tier1_codes || []).join(" · ")}</p>
                </div>
              ) : null}
              <div style={{ ...toolbarStyle, marginBottom: 8 }}>
                <button type="button" style={buttonGhostStyle} onClick={() => void onSeedPlayers()}>
                  Seed catalogo global
                </button>
                <input
                  style={{ ...healthLocalFilterInputStyle, maxWidth: 220 }}
                  placeholder="Filtrar player…"
                  value={playerFilter}
                  onChange={(e) => setPlayerFilter(e.target.value)}
                />
              </div>
              <div style={cardStyle}>
                <DataTable
                  columns={[
                    { key: "code", label: "Codigo" },
                    { key: "name", label: "Nome" },
                    { key: "player_role", label: "Papel" },
                    { key: "country", label: "Pais" },
                    { key: "bi_priority_score", label: "Score BI" },
                  ]}
                  rows={filteredPlayers}
                />
              </div>
              <div style={{ ...cardStyle, marginTop: 10 }}>
                <h4 style={{ margin: "0 0 8px" }}>Relacoes ({relations.length})</h4>
                <JsonBlock data={relations} maxHeight={200} />
              </div>
            </div>
          ) : null}

          {tab === "taxonomy" ? (
            <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
              <div style={cardStyle}>
                <h4 style={{ margin: "0 0 8px" }}>Segmentos</h4>
                <DataTable
                  columns={[
                    { key: "code", label: "Codigo" },
                    { key: "label", label: "Label" },
                  ]}
                  rows={taxonomy}
                />
              </div>
              <div style={cardStyle}>
                <h4 style={{ margin: "0 0 8px" }}>Presenca de mercado</h4>
                <DataTable
                  columns={[
                    { key: "network_player_code", label: "Player" },
                    { key: "country_code", label: "Pais" },
                    { key: "locker_count_est", label: "Lockers est." },
                  ]}
                  rows={marketPresence}
                />
              </div>
            </div>
          ) : null}

          {tab === "webhooks" ? (
            <div style={{ marginTop: 14 }}>
              <form
                onSubmit={(e) => void onCreateWebhook(e)}
                style={{
                  ...cardStyle,
                  display: "grid",
                  gap: 8,
                  gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                  marginBottom: 10,
                }}
              >
                <input
                  style={healthLocalFilterInputStyle}
                  value={webhookForm.network_player_code}
                  onChange={(e) => setWebhookForm({ ...webhookForm, network_player_code: e.target.value })}
                />
                <input
                  style={healthLocalFilterInputStyle}
                  value={webhookForm.capability_code}
                  onChange={(e) => setWebhookForm({ ...webhookForm, capability_code: e.target.value })}
                />
                <input
                  style={healthLocalFilterInputStyle}
                  placeholder="URL"
                  value={webhookForm.url}
                  onChange={(e) => setWebhookForm({ ...webhookForm, url: e.target.value })}
                  required
                />
                <button type="submit" style={buttonPrimaryStyle}>
                  Registrar webhook
                </button>
              </form>
              <div style={cardStyle}>
                <JsonBlock data={webhooks} />
              </div>
            </div>
          ) : null}

          {tab === "audit" ? (
            <div style={{ ...cardStyle, marginTop: 14 }}>
              <DataTable
                columns={[
                  { key: "event_type", label: "Evento" },
                  { key: "summary", label: "Resumo" },
                  { key: "created_at", label: "Quando" },
                ]}
                rows={audit}
              />
            </div>
          ) : null}

          {tab === "integration" ? (
            <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
              <div style={cardStyle}>
                <h4 style={{ margin: "0 0 8px" }}>Integration hub</h4>
                <JsonBlock data={integrationLinks} maxHeight={180} />
              </div>
              <div style={cardStyle}>
                <h4 style={{ margin: "0 0 8px" }}>Dominios unificados</h4>
                <DataTable
                  columns={[
                    { key: "domain_code", label: "Dominio" },
                    { key: "label", label: "Label" },
                    {
                      key: "admin_route",
                      label: "Rota OPS",
                      render: (r) =>
                        r.admin_route ? (
                          <Link to={r.admin_route} style={{ color: "#93c5fd" }}>
                            {r.admin_route}
                          </Link>
                        ) : (
                          "—"
                        ),
                    },
                  ]}
                  rows={domainLinks}
                />
              </div>
              <p style={summary24hHintStyle}>analytics-service (8127) · ml-admin (8021) · analytics-bi-admin (8026)</p>
            </div>
          ) : null}

          {loading && tab !== "overview" ? <p style={{ ...mutedTextStyle, marginTop: 12 }}>Carregando aba…</p> : null}
        </section>
      </section>
    </div>
  );
}

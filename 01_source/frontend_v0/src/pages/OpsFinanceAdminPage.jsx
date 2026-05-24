
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import {
  apiKeyBannerStyle,
  buttonGhostStyle,
  buttonPrimaryStyle,
  cardStyle,
  crossShortcutLinkStyle,
  healthLocalFilterFieldStyle,
  healthLocalFilterInputStyle,
  healthLocalFilterRowStyle,
  mutedTextStyle,
  okBannerStyle,
  opsSanityCardStyle,
  pageStyle,
  summary24hHeaderStyle,
  tabButtonStyle,
  tableStyle,
  tdStyle,
  thStyle,
  toolbarStyle,
} from "../styles/opsShellStyles";

const BASE = import.meta.env.VITE_FINANCE_ADMIN_BASE_URL || "/api/fna";
const API = `${BASE}/v1/finance-admin`;
const PAGE_VERSION = "ops/finance/admin v0.4-professional";
const NETWORK_SEGMENTS = [
  "",
  "LOCKER_NETWORK",
  "LOCKER_NETWORK_OPERATOR",
  "CARRIER_LAST_MILE",
  "MARKETPLACE",
  "COLLECTION_POINT",
  "LOGISTICS_PLATFORM",
  "FOOD_DELIVERY",
  "PAYMENTS_FISCAL",
];

const TAB_DEFS = [
  ["networks", "Redes mundiais"],
  ["intelligence", "Inteligência"],
  ["ecosystem", "Ecossistema"],
  ["readiness", "Readiness"],
  ["roadmap", "Roadmap"],
  ["contracts", "Contratos"],
  ["slas", "SLAs"],
  ["revrec", "Rev. receita"],
  ["jobs", "Jobs"],
  ["partners", "Parceiros"],
  ["billing", "Billing"],
  ["invoices", "NF B2B"],
  ["settlements", "Settlements"],
  ["treasury", "Treasury"],
  ["wallet", "Wallet"],
  ["pnl", "PnL"],
  ["reconciliation", "Gaps"],
  ["webhooks", "DLQ"],
  ["ops", "Ops"],
];

function parseError(payload, fallback = "Falha na API finance-admin.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  return fallback;
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao (${endpoint}). Verifique proxy ${BASE} (porta 8123).`;
  }
  return raw;
}

export default function OpsFinanceAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao") || hasRole("admin.financeiro");
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get("tab") || "networks";
  const setTab = (k) => setSearchParams({ tab: k }, { replace: true });
  const [networkCatalog, setNetworkCatalog] = useState([]);
  const [networkStats, setNetworkStats] = useState({});
  const [worldPriorityIndex, setWorldPriorityIndex] = useState([]);
  const [integrationGuide, setIntegrationGuide] = useState(null);
  const [intelDash, setIntelDash] = useState(null);
  const [networkFilter, setNetworkFilter] = useState("");
  const [partners, setPartners] = useState([]);
  const [plans, setPlans] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [lineItems, setLineItems] = useState([]);
  const [b2b, setB2b] = useState([]);
  const [settlements, setSettlements] = useState([]);
  const [credits, setCredits] = useState([]);
  const [holds, setHolds] = useState([]);
  const [commissions, setCommissions] = useState([]);
  const [costCenters, setCostCenters] = useState([]);
  const [ccMonthly, setCcMonthly] = useState([]);
  const [gaps, setGaps] = useState([]);
  const [deliveries, setDeliveries] = useState([]);
  const [walletProviders, setWalletProviders] = useState([]);
  const [walletTx, setWalletTx] = useState([]);
  const [opsInvoices, setOpsInvoices] = useState([]);
  const [events, setEvents] = useState([]);
  const [ecosystemSummary, setEcosystemSummary] = useState(null);
  const [playerRelations, setPlayerRelations] = useState([]);
  const [readiness, setReadiness] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [slaDefs, setSlaDefs] = useState([]);
  const [slaBreaches, setSlaBreaches] = useState([]);
  const [revenueSchedules, setRevenueSchedules] = useState([]);
  const [revenueEntries, setRevenueEntries] = useState([]);
  const [jobRuns, setJobRuns] = useState([]);
  const [partnerForm, setPartnerForm] = useState({ code: "", name: "", partner_type: "ECOMMERCE" });
  const [selectedId, setSelectedId] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [lastApiKey, setLastApiKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const headers = useMemo(
    () => ({
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }),
    [token],
  );

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErr("");
    setOk("");
    try {
      const failedOnly = tab === "webhooks" ? "true" : "false";
      const catalogUrl = networkFilter
        ? `${API}/locker-network-catalog?segment_code=${encodeURIComponent(networkFilter)}`
        : `${API}/locker-network-catalog`;
      const urls = [
        catalogUrl,
        `${API}/finance-partners`,
        `${API}/billing-plans`,
        `${API}/billing-cycles`,
        `${API}/billing-line-items`,
        `${API}/b2b-invoices`,
        `${API}/settlement-batches`,
        `${API}/credit-notes`,
        `${API}/payment-holds`,
        `${API}/commission-structures`,
        `${API}/cost-centers`,
        `${API}/cost-center-monthly`,
        `${API}/fiscal-reconciliation-gaps`,
        `${API}/webhook-deliveries?failed_only=${failedOnly}`,
        `${API}/wallet-providers`,
        `${API}/wallet-transactions`,
        `${API}/ops-invoices`,
        `${API}/billing-processed-events`,
        `${API}/locker-network-catalog/ecosystem-summary`,
        `${API}/locker-network-catalog/relations`,
        `${API}/partner-readiness`,
        `${API}/integration-milestones`,
        `${API}/commercial-contracts`,
        `${API}/sla-definitions`,
        `${API}/sla-breaches`,
        `${API}/revenue-schedules`,
        `${API}/revenue-recognition-entries`,
        `${API}/jobs/runs`,
        `${API}/locker-network-catalog/world-priority-index`,
      ];
      const res = await Promise.all(urls.map((u) => fetch(u, { headers })));
      const jsons = await Promise.all(res.map((r) => r.json().catch(() => ({}))));
      const pick = (idx, key = "items", extra) => {
        if (res[idx]?.ok) {
          if (extra) extra(jsons[idx]);
          return jsons[idx][key] || [];
        }
        return [];
      };
      setNetworkCatalog(pick(0));
      if (res[0]?.ok) setNetworkStats(jsons[0].by_parent_group || {});
      else setNetworkStats({});
      setPartners(pick(1));
      setPlans(pick(2));
      setCycles(pick(3));
      setLineItems(pick(4));
      setB2b(pick(5));
      setSettlements(pick(6));
      setCredits(pick(7));
      setHolds(pick(8));
      setCommissions(pick(9));
      setCostCenters(pick(10));
      setCcMonthly(pick(11));
      setGaps(pick(12));
      setDeliveries(pick(13));
      setWalletProviders(pick(14));
      setWalletTx(pick(15));
      setOpsInvoices(pick(16));
      setEvents(pick(17));
      if (res[18]?.ok) setEcosystemSummary(jsons[18]);
      else setEcosystemSummary(null);
      setPlayerRelations(pick(19));
      setReadiness(pick(20));
      setMilestones(pick(21));
      setContracts(pick(22));
      setSlaDefs(pick(23));
      setSlaBreaches(pick(24));
      setRevenueSchedules(pick(25));
      setRevenueEntries(pick(26));
      setJobRuns(pick(27));
      if (res[28]?.ok) setWorldPriorityIndex(jsons[28].items || []);
      else setWorldPriorityIndex([]);

      const failed = res.map((r, i) => (!r.ok ? urls[i].replace(`${API}/`, "") : null)).filter(Boolean);
      if (!res.some((r) => r.ok)) {
        throw new Error(
          `Servico finance-admin indisponivel em ${BASE}. Inicie: cd 01_source/finance_admin_service && PYTHONPATH=. .venv/bin/uvicorn app.main:app --port 8123`,
        );
      }
      if (failed.length) {
        setOk(
          `Dados parciais (${failed.length} endpoint(s) 404). Reinicie o finance-admin na porta 8123 (versao atual) e clique Seed.`,
        );
      }
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  }, [token, headers, tab, networkFilter]);

  const loadIntegrationGuide = async (code) => {
    if (!token || !code) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/locker-network-catalog/players/${encodeURIComponent(code)}/integration-guide`, {
        headers,
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setIntegrationGuide(j);
    } catch (e) {
      setIntegrationGuide(null);
      setErr(normalizeNetworkError(e, `${API}/locker-network-catalog/players/.../integration-guide`));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [load]);

  const onSyncCatalog = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/locker-network-catalog/sync`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Catálogo sincronizado: ${j.catalog_upserted} players.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/locker-network-catalog/sync`));
    } finally {
      setLoading(false);
    }
  };

  const onSeed = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seed`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Seed financeiro aplicado.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seed`));
    } finally {
      setLoading(false);
    }
  };

  const onCreatePartner = async () => {
    if (!token || !canMutate || !partnerForm.code || !partnerForm.name) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/finance-partners`, {
        method: "POST",
        headers,
        body: JSON.stringify(partnerForm),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Parceiro ${j.code} criado.`);
      setSelectedId(j.id);
      setPartnerForm({ code: "", name: "", partner_type: "ECOMMERCE" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/finance-partners`));
    } finally {
      setLoading(false);
    }
  };

  const onWebhook = async () => {
    if (!token || !canMutate || !selectedId || !webhookUrl) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/finance-partners/${encodeURIComponent(selectedId)}/webhook`, {
        method: "PUT",
        headers,
        body: JSON.stringify({
          url: webhookUrl,
          secret: webhookSecret || undefined,
          events: ["billing.cycle.closed", "invoice.issued"],
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Webhook salvo.");
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/finance-partners/.../webhook`));
    } finally {
      setLoading(false);
    }
  };

  const onRotate = async () => {
    if (!token || !canMutate || !selectedId) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/finance-partners/${encodeURIComponent(selectedId)}/api-keys/rotate`, {
        method: "POST",
        headers,
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setLastApiKey(j.api_key || "");
      setOk(`Nova API key (${j.key_prefix}…). Copie agora.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/finance-partners/.../api-keys/rotate`));
    } finally {
      setLoading(false);
    }
  };

  const onAnalyzeIntel = async () => {
    if (!token) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/ecosystem-intelligence/analyze`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      const d = await fetch(`${API}/ecosystem-intelligence/dashboard`, { headers });
      const dj = await d.json().catch(() => ({}));
      if (d.ok) setIntelDash(dj);
      setOk(`Inteligência: ${j.insights_created} insights · ${j.benchmarks_computed} benchmarks`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/ecosystem-intelligence/analyze`));
    } finally {
      setLoading(false);
    }
  };

  const onRecomputeReadiness = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/partner-readiness/recompute`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Readiness: ${j.recomputed} players · média ${j.average_score}`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/partner-readiness/recompute`));
    } finally {
      setLoading(false);
    }
  };

  const tableRows =
    tab === "ecosystem"
      ? [
          ...(ecosystemSummary
            ? [
                {
                  key: "eco",
                  tipo: "KPI",
                  id: "summary",
                  detalhe: `${ecosystemSummary.total_players} players · ${ecosystemSummary.live_count} LIVE · readiness ${ecosystemSummary.readiness_average}`,
                },
              ]
            : []),
          ...playerRelations.map((rel) => ({
            key: rel.id,
            tipo: rel.relation_type,
            id: `${rel.from_catalog_code}→${rel.to_catalog_code}`,
            detalhe: rel.notes || "—",
          })),
        ]
      : tab === "readiness"
        ? readiness.map((r) => ({
            key: r.catalog_code,
            tipo: r.grade,
            id: r.catalog_code,
            detalhe: `score ${r.readiness_score} · ${r.blockers_json}`,
          }))
        : tab === "roadmap"
          ? milestones.map((m) => ({
              key: m.id,
              tipo: m.phase,
              id: m.catalog_code,
              detalhe: `${m.title} · ${m.status} · ${m.target_date || "—"}`,
            }))
          : tab === "contracts"
            ? contracts.map((c) => ({
                key: c.id,
                tipo: c.contract_type,
                id: c.catalog_code || "—",
                detalhe: `${c.title} · ${c.status}`,
              }))
            : tab === "revrec"
              ? [
                  ...revenueSchedules.map((s) => ({
                    key: s.id,
                    tipo: "schedule",
                    id: s.source_id,
                    detalhe: `total ${s.total_cents} · def ${s.deferred_cents}`,
                  })),
                  ...revenueEntries.map((e) => ({
                    key: e.id,
                    tipo: "entry",
                    id: e.recognition_date,
                    detalhe: `${e.amount_cents} centavos`,
                  })),
                ]
              : tab === "jobs"
                ? jobRuns.map((j) => ({
                    key: j.id,
                    tipo: j.job_code,
                    id: j.status,
                    detalhe: j.error_message || j.started_at || "—",
                  }))
            : tab === "slas"
              ? [
                  ...slaDefs.map((s) => ({
                    key: `sla-${s.id}`,
                    tipo: "def",
                    id: s.metric_code,
                    detalhe: `${s.metric_name} · meta ${s.target_value}`,
                  })),
                  ...slaBreaches.map((b) => ({
                    key: `br-${b.id}`,
                    tipo: "breach",
                    id: b.sla_id?.slice(0, 8),
                    detalhe: `${b.status} · obs ${b.observed_value}`,
                  })),
                ]
      : tab === "networks"
      ? networkCatalog.map((n) => ({
          key: n.id,
          tipo: n.parent_group,
          id: n.code,
          detalhe: `${n.name} · ${n.country_code} · ${n.integration_status} · fin:${n.finance_partner_code || "—"}`,
        }))
      : tab === "partners"
      ? partners.map((p) => ({
          key: p.id,
          tipo: "partner",
          id: p.code,
          detalhe: `${p.name} · ${p.partner_type} · ${p.active ? "ativo" : "off"}`,
        }))
      : tab === "billing"
        ? [
            ...plans.map((pl) => ({
              key: `pl-${pl.id}`,
              tipo: "plano",
              id: pl.plan_name,
              detalhe: `${pl.billing_model} · partner ${pl.partner_id?.slice(0, 8)}`,
            })),
            ...cycles.map((c) => ({
              key: `cy-${c.id}`,
              tipo: "ciclo",
              id: c.status,
              detalhe: `${c.period_start} → ${c.period_end} · ${c.total_amount_cents} centavos`,
            })),
            ...lineItems.map((li) => ({
              key: `li-${li.id}`,
              tipo: "line",
              id: li.line_type,
              detalhe: `${li.description} · ${li.total_cents}`,
            })),
          ]
        : tab === "invoices"
          ? b2b.map((i) => ({
              key: i.id,
              tipo: "b2b",
              id: i.invoice_number || i.id.slice(0, 8),
              detalhe: `${i.status} · ${i.amount_cents} centavos`,
            }))
          : tab === "settlements"
            ? settlements.map((s) => ({
                key: s.id,
                tipo: "batch",
                id: s.status,
                detalhe: `net ${s.net_amount_cents} · gross ${s.gross_revenue_cents}`,
              }))
            : tab === "treasury"
              ? [
                  ...credits.map((c) => ({ key: `cr-${c.id}`, tipo: "credito", id: c.reason_code, detalhe: `${c.status} · ${c.amount_cents}` })),
                  ...holds.map((h) => ({ key: `ho-${h.id}`, tipo: "hold", id: h.status, detalhe: String(h.hold_amount_cents) })),
                  ...commissions.map((c) => ({
                    key: `cm-${c.id}`,
                    tipo: "comissao",
                    id: String(c.commission_percentage),
                    detalhe: c.partner_id?.slice(0, 8),
                  })),
                ]
              : tab === "wallet"
                ? [
                    ...walletProviders.map((w) => ({ key: `wp-${w.id}`, tipo: "wallet", id: w.code, detalhe: w.name })),
                    ...walletTx.map((t) => ({ key: `wt-${t.id}`, tipo: "tx", id: t.type, detalhe: `${t.amount_cents} · ${t.status}` })),
                  ]
                : tab === "pnl"
                  ? [
                      ...costCenters.map((c) => ({ key: `cc-${c.locker_id}`, tipo: "locker", id: c.locker_id, detalhe: c.network_code || "—" })),
                      ...ccMonthly.map((m) => ({
                        key: `ccm-${m.id}`,
                        tipo: "mensal",
                        id: m.locker_id,
                        detalhe: `${m.month} · costs ${m.total_costs_cents}`,
                      })),
                    ]
                  : tab === "reconciliation"
                    ? gaps.map((g) => ({
                        key: g.id,
                        tipo: g.gap_type,
                        id: g.severity,
                        detalhe: `${g.status} · ${g.order_id || "—"}`,
                      }))
                    : tab === "webhooks"
                      ? deliveries.map((d) => ({
                          key: d.id,
                          tipo: "delivery",
                          id: d.event_type,
                          detalhe: `${d.status} · HTTP ${d.http_status ?? "—"}`,
                        }))
                      : [
                          ...opsInvoices.map((o) => ({
                            key: `oi-${o.id}`,
                            tipo: "nf-ops",
                            id: o.order_id,
                            detalhe: `${o.status} · ${o.country}`,
                          })),
                          ...events.map((e) => ({
                            key: `ev-${e.id}`,
                            tipo: "event",
                            id: e.event_type,
                            detalhe: e.event_id,
                          })),
                        ];

  const listCount = tableRows.length;

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10, gap: 8 }}>
          <Link to="/ops/payment-gateway/admin" style={crossShortcutLinkStyle}>
            Payment Gateway
          </Link>
          <Link to="/ops/partners/admin?tab=billing" style={crossShortcutLinkStyle}>
            Partners billing
          </Link>
          <Link to="/ops/billing/kpis" style={crossShortcutLinkStyle}>
            Billing KPIs
          </Link>
        </div>

        <OpsPageTitleHeader
          title="OPS — Finance Admin"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Parceiros financeiros, planos/ciclos B2B, wallet, NF ops e eventos billing —{" "}
          <code style={{ color: "#e2e8f0" }}>{API}</code>
        </p>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Dominio FINANCE</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {TAB_DEFS.map(([k, label]) => (
                <button key={k} type="button" style={tabButtonStyle(tab === k)} onClick={() => setTab(k)}>
                  {label}
                </button>
              ))}
            </div>
          </div>

          {tab === "networks" ? (
            <>
              <div
                style={{
                  marginBottom: 8,
                  padding: "8px 10px",
                  borderRadius: 8,
                  border: "1px solid rgba(99,102,241,0.35)",
                  background: "rgba(99,102,241,0.08)",
                }}
              >
                <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6, color: "#c7d2fe" }}>
                  Players prioritários (world-priority-index)
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {worldPriorityIndex.length === 0 ? (
                    <span style={{ ...mutedTextStyle, fontSize: 11 }}>Sync catálogo para carregar o índice.</span>
                  ) : (
                    worldPriorityIndex.map((p) => (
                      <button
                        key={p.code}
                        type="button"
                        title={`${p.segment} · ${(p.countries || []).join(", ")}`}
                        style={{
                          fontSize: 11,
                          padding: "2px 8px",
                          borderRadius: 6,
                          border: "none",
                          cursor: "pointer",
                          background: networkCatalog.some((n) => n.code === p.code) ? "#4f46e5" : "rgba(245,158,11,0.25)",
                          color: networkCatalog.some((n) => n.code === p.code) ? "#fff" : "#fcd34d",
                        }}
                        onClick={() => void loadIntegrationGuide(p.code)}
                      >
                        {p.code} · {(p.countries || []).join("/")}
                      </button>
                    ))
                  )}
                </div>
              </div>
              <div style={{ ...healthLocalFilterRowStyle, alignItems: "center", gap: 6 }}>
                <span style={{ ...mutedTextStyle, fontSize: 12 }}>Segmento:</span>
                {NETWORK_SEGMENTS.map((g) => (
                  <button
                    key={g || "all"}
                    type="button"
                    style={tabButtonStyle(networkFilter === g)}
                    onClick={() => setNetworkFilter(g)}
                  >
                    {g || "Todos"}
                    {g && networkStats[g] != null ? ` (${networkStats[g]})` : ""}
                  </button>
                ))}
              </div>
            </>
          ) : null}

          {tab === "networks" && integrationGuide ? (
            <div
              style={{
                marginBottom: 10,
                padding: 12,
                borderRadius: 8,
                border: "1px solid rgba(148,163,184,0.35)",
                background: "rgba(15,23,42,0.5)",
                fontSize: 12,
              }}
            >
              <strong>
                Como integrar · {integrationGuide.name} ({integrationGuide.catalog_code})
              </strong>
              {integrationGuide.blueprint ? (
                <p style={{ margin: "6px 0", color: "#c7d2fe" }}>
                  Blueprint {integrationGuide.blueprint.code}: {integrationGuide.blueprint.primary_capability} ·{" "}
                  {integrationGuide.blueprint.auth_type}
                </p>
              ) : null}
              <ul style={{ margin: "6px 0", paddingLeft: 18 }}>
                {(integrationGuide.integration_steps || []).slice(0, 5).map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
              <p style={{ margin: 0, color: "#94a3b8" }}>
                Relações: {(integrationGuide.relations || []).length} · Cobertura:{" "}
                {(integrationGuide.country_coverage || []).length}
                {integrationGuide.readiness
                  ? ` · Readiness ${integrationGuide.readiness.readiness_score} (${integrationGuide.readiness.grade})`
                  : ""}
              </p>
              <button type="button" style={{ ...buttonGhostStyle, marginTop: 8 }} onClick={() => setIntegrationGuide(null)}>
                Fechar
              </button>
            </div>
          ) : null}

          {tab === "partners" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                code
                <input
                  value={partnerForm.code}
                  onChange={(e) => setPartnerForm((f) => ({ ...f, code: e.target.value.toUpperCase() }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="DPD"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                name
                <input
                  value={partnerForm.name}
                  onChange={(e) => setPartnerForm((f) => ({ ...f, name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                tipo
                <select
                  value={partnerForm.partner_type}
                  onChange={(e) => setPartnerForm((f) => ({ ...f, partner_type: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="ECOMMERCE">ECOMMERCE</option>
                  <option value="CARRIER">CARRIER</option>
                  <option value="LOGISTICS">LOGISTICS</option>
                </select>
              </label>
            </div>
          ) : null}

          {tab === "partners" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                parceiro
                <select
                  value={selectedId}
                  onChange={(e) => setSelectedId(e.target.value)}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="">—</option>
                  {partners.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.code}
                    </option>
                  ))}
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                webhook URL
                <input value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} style={healthLocalFilterInputStyle} />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                secret
                <input value={webhookSecret} onChange={(e) => setWebhookSecret(e.target.value)} style={healthLocalFilterInputStyle} />
              </label>
            </div>
          ) : null}

          {tab === "intelligence" && intelDash ? (
            <p style={{ ...mutedTextStyle, fontSize: 12, marginBottom: 8 }}>
              {intelDash.open_insights} insights abertos · {intelDash.critical_insights} críticos · readiness médio{" "}
              {intelDash.avg_readiness} · composite {intelDash.avg_composite_score}
            </p>
          ) : null}

          <div style={toolbarStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => load()} disabled={loading || !token}>
              Recarregar
            </button>
            {canMutate ? (
              <>
                <button type="button" style={buttonGhostStyle} onClick={onSyncCatalog} disabled={loading}>
                  Sync catálogo
                </button>
                <button type="button" style={buttonPrimaryStyle} onClick={onSeed} disabled={loading}>
                  Seed
                </button>
                {tab === "readiness" ? (
                  <button type="button" style={buttonGhostStyle} onClick={onRecomputeReadiness} disabled={loading}>
                    Recompute readiness
                  </button>
                ) : null}
                {tab === "intelligence" ? (
                  <button type="button" style={buttonPrimaryStyle} onClick={() => void onAnalyzeIntel()} disabled={loading}>
                    Scan inteligência
                  </button>
                ) : null}
                {tab === "partners" ? (
                  <>
                    <button type="button" style={buttonPrimaryStyle} onClick={onCreatePartner} disabled={loading}>
                      Criar parceiro
                    </button>
                    <button type="button" style={buttonGhostStyle} onClick={onWebhook} disabled={loading}>
                      Webhook
                    </button>
                    <button type="button" style={buttonGhostStyle} onClick={onRotate} disabled={loading}>
                      Rotacionar API key
                    </button>
                  </>
                ) : null}
              </>
            ) : null}
          </div>

          {ok ? <div style={okBannerStyle}>{ok}</div> : null}
          {err ? <div style={{ ...okBannerStyle, background: "#3f1d1d", color: "#fecaca" }}>{err}</div> : null}
          {lastApiKey ? <div style={apiKeyBannerStyle}>{lastApiKey}</div> : null}

          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>tipo</th>
                <th style={thStyle}>id</th>
                <th style={thStyle}>detalhe</th>
              </tr>
            </thead>
            <tbody>
              {tableRows.map((row) => (
                <tr key={row.key}>
                  <td style={tdStyle}>{row.tipo}</td>
                  <td style={tdStyle}>{row.id}</td>
                  <td style={tdStyle}>{row.detalhe}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p style={mutedTextStyle}>{listCount} registro(s) · aba {tab}</p>
        </section>
      </section>
    </div>
  );
}

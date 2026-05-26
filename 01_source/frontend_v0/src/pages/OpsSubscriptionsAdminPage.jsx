
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import {
  apiKeyBannerStyle,
  buttonGhostStyle,
  buttonPrimaryStyle,
  cardStyle,
  criticalBannerStyle,
  crossShortcutLinkStyle,
  healthLocalFilterFieldStyle,
  healthLocalFilterInputStyle,
  healthLocalFilterRowStyle,
  mutedTextStyle,
  okBannerStyle,
  opsSanityCardStyle,
  pageStyle,
  tabButtonStyle,
  tableStyle,
  tdStyle,
  thStyle,
  toolbarStyle,
} from "../styles/opsShellStyles";

const BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const API = `${BASE}/v1/subscriptions-admin`;
const V1_SUBSCRIPTIONS_HUB =
  (import.meta.env.VITE_OPS_CONSOLE_URL || "http://localhost:5173/v1").replace(/\/$/, "") +
  "/ops/subscriptions/admin";
const PAGE_VERSION = "ops/subscriptions/admin v2.0";

const TAB_GROUPS = [
  {
    id: "hub",
    label: "Hub & analytics",
    tabs: [
      { id: "overview", label: "Visão geral" },
      { id: "analytics", label: "Analytics" },
      { id: "ecosystem", label: "Ecossistema" },
    ],
  },
  {
    id: "catalog",
    label: "Planos & catálogo",
    tabs: [
      { id: "plans", label: "Planos" },
      { id: "entitlements", label: "Entitlements" },
      { id: "partners", label: "Parceiros B2B" },
    ],
  },
  {
    id: "ops",
    label: "Operação",
    tabs: [
      { id: "subscriptions", label: "Assinaturas" },
      { id: "benefits", label: "Benefícios" },
      { id: "billing", label: "Faturamento" },
      { id: "events", label: "Eventos" },
      { id: "dunning", label: "Dunning" },
    ],
  },
  {
    id: "integrations",
    label: "Integrações",
    tabs: [
      { id: "integrations", label: "Webhooks & keys" },
      { id: "deliveries", label: "Entregas webhook" },
      { id: "relations", label: "Relações" },
      { id: "food_delivery", label: "Food delivery" },
    ],
  },
  {
    id: "growth",
    label: "Growth",
    tabs: [
      { id: "premium", label: "Premium" },
      { id: "global", label: "Global" },
      { id: "efficiency", label: "Eficiência" },
    ],
  },
];

const ALL_TABS = TAB_GROUPS.flatMap((g) => g.tabs);

function groupForTab(tabId) {
  return TAB_GROUPS.find((g) => g.tabs.some((t) => t.id === tabId))?.id ?? TAB_GROUPS[0].id;
}

function parseError(payload, fallback = "Falha na API subscriptions.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail?.message) return String(payload.detail.message);
  if (payload?.detail?.type) return `${payload.detail.type}: ${payload.detail.message || ""}`;
  return fallback;
}

function formatBrl(cents) {
  const n = Number(cents);
  if (!Number.isFinite(n)) return "—";
  return `R$ ${(n / 100).toFixed(2)}`;
}

function statusPill(status) {
  const s = String(status || "").toUpperCase();
  const base = {
    display: "inline-block",
    padding: "2px 8px",
    borderRadius: 999,
    fontSize: 11,
    fontWeight: 700,
  };
  if (s === "ACTIVE") return { ...base, background: "rgba(34,197,94,0.25)", color: "#86efac" };
  if (s === "TRIALING") return { ...base, background: "rgba(56,189,248,0.25)", color: "#7dd3fc" };
  if (s === "PAST_DUE") return { ...base, background: "rgba(251,191,36,0.25)", color: "#fcd34d" };
  if (s === "CANCELLED") return { ...base, background: "rgba(100,116,139,0.35)", color: "#cbd5e1" };
  return { ...base, background: "rgba(100,116,139,0.2)", color: "#94a3b8" };
}

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    credentials: "include",
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(parseError(data, `HTTP ${res.status}`));
  return data;
}

function SectionTitle({ children, hint }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <h3 style={{ margin: 0, fontSize: 15, color: "#e2e8f0" }}>{children}</h3>
      {hint ? <p style={{ ...mutedTextStyle, marginTop: 4, fontSize: 12 }}>{hint}</p> : null}
    </div>
  );
}

function EmptyRow({ colSpan, message }) {
  return (
    <tr>
      <td colSpan={colSpan} style={{ ...tdStyle, textAlign: "center", color: "#94a3b8", padding: 24 }}>
        {message}
      </td>
    </tr>
  );
}

function KpiGrid({ items }) {
  return (
    <div
      style={{
        marginTop: 16,
        display: "grid",
        gap: 12,
        gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
      }}
    >
      {items.map(([label, val]) => (
        <div key={label} style={{ ...cardStyle, padding: 12 }}>
          <div style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.04em" }}>
            {label}
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, color: "#f8fafc", marginTop: 6 }}>{val}</div>
        </div>
      ))}
    </div>
  );
}

export default function OpsSubscriptionsAdminPage() {
  const { hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get("tab") || "overview";
  const safeTab = ALL_TABS.some((t) => t.id === initialTab) ? initialTab : "overview";

  const [tabGroup, setTabGroup] = useState(() => groupForTab(safeTab));
  const [tab, setTab] = useState(safeTab);
  const [summary, setSummary] = useState(null);
  const [plans, setPlans] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [benefits, setBenefits] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [apiKeys, setApiKeys] = useState([]);
  const [catalog, setCatalog] = useState(null);
  const [priorityPlayers, setPriorityPlayers] = useState([]);
  const [relations, setRelations] = useState([]);
  const [foodHandoffs, setFoodHandoffs] = useState([]);
  const [trends, setTrends] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [events, setEvents] = useState([]);
  const [partnerPrograms, setPartnerPrograms] = useState([]);
  const [entitlements, setEntitlements] = useState([]);
  const [dunningCases, setDunningCases] = useState([]);
  const [deliveries, setDeliveries] = useState([]);
  const [churnAlerts, setChurnAlerts] = useState([]);
  const [referrals, setReferrals] = useState([]);
  const [worldSummary, setWorldSummary] = useState(null);
  const [regionalPrices, setRegionalPrices] = useState([]);
  const [addonCatalog, setAddonCatalog] = useState([]);
  const [retentionOffers, setRetentionOffers] = useState([]);
  const [settlements, setSettlements] = useState([]);
  const [efficiencySummary, setEfficiencySummary] = useState(null);
  const [opsInbox, setOpsInbox] = useState([]);
  const [promoCodes, setPromoCodes] = useState([]);
  const [upgradeSuggestions, setUpgradeSuggestions] = useState([]);
  const [automationRules, setAutomationRules] = useState([]);
  const [usageMeters, setUsageMeters] = useState([]);
  const [inboxBulkOps, setInboxBulkOps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const [lastApiKey, setLastApiKey] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [webhookPartner, setWebhookPartner] = useState("magalu");
  const [webhookUrl, setWebhookUrl] = useState("https://hooks.example.com/subscriptions");
  const [subForm, setSubForm] = useState({ user_id: "", plan_type: "PREMIUM", partner_code: "", promo_code: "" });
  const [promoForm, setPromoForm] = useState({
    code: "",
    description: "",
    discount_pct: 10,
    eligible_plans: "BASIC,PREMIUM",
    max_redemptions: 100,
  });
  const [ruleForm, setRuleForm] = useState({
    rule_code: "",
    name: "",
    trigger_event: "subscription.past_due",
    action_type: "ISSUE_RETENTION_OFFER",
  });
  const [showPromoForm, setShowPromoForm] = useState(false);
  const [showRuleForm, setShowRuleForm] = useState(false);

  const activeGroup = useMemo(() => TAB_GROUPS.find((g) => g.id === tabGroup) ?? TAB_GROUPS[0], [tabGroup]);

  useEffect(() => {
    const fromUrl = searchParams.get("tab") || "overview";
    const nextTab = ALL_TABS.some((t) => t.id === fromUrl) ? fromUrl : "overview";
    setTab(nextTab);
    setTabGroup(groupForTab(nextTab));
  }, [searchParams]);

  const setTabUrl = (id) => {
    setTab(id);
    setTabGroup(groupForTab(id));
    const next = new URLSearchParams(searchParams);
    if (id === "overview") next.delete("tab");
    else next.set("tab", id);
    setSearchParams(next, { replace: true });
  };

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const subQ = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : "";
      const [
        m,
        p,
        s,
        b,
        w,
        k,
        eco,
        pri,
        rel,
        fh,
        tr,
        inv,
        ev,
        pp,
        ent,
        dun,
        del,
        churn,
        refs,
        wsum,
        reg,
        addons,
        ret,
        sett,
        esum,
        inbox,
        promos,
        upgrades,
        rules,
        meters,
      ] = await Promise.all([
        apiFetch("/metrics/summary"),
        apiFetch("/plans?active_only=false"),
        apiFetch(`/subscriptions${subQ}`),
        apiFetch("/benefits-usage"),
        apiFetch("/webhooks"),
        apiFetch("/api-keys"),
        apiFetch("/ecosystem/catalog"),
        apiFetch("/players/priority"),
        apiFetch("/ecosystem/relations"),
        apiFetch("/ecosystem/food-handoffs"),
        apiFetch("/metrics/trends?months=6"),
        apiFetch("/invoices"),
        apiFetch("/events"),
        apiFetch("/partner-programs"),
        apiFetch("/entitlements"),
        apiFetch("/dunning"),
        apiFetch("/webhook-deliveries"),
        apiFetch("/churn/alerts"),
        apiFetch("/referrals"),
        apiFetch("/world/summary"),
        apiFetch("/world/regional-prices"),
        apiFetch("/world/addons/catalog"),
        apiFetch("/world/retention-offers"),
        apiFetch("/world/settlements"),
        apiFetch("/efficiency/summary"),
        apiFetch("/efficiency/ops-inbox"),
        apiFetch("/efficiency/promo-codes"),
        apiFetch("/efficiency/upgrade-matrix"),
        apiFetch("/efficiency/automation-rules"),
        apiFetch("/efficiency/usage-meters"),
      ]);
      setSummary(m.summary || null);
      setPlans(p.items || []);
      setSubscriptions(s.items || []);
      setBenefits(b.items || []);
      setWebhooks(w.items || []);
      setApiKeys(k.items || []);
      setCatalog(eco.catalog || null);
      setPriorityPlayers(pri.items || []);
      setRelations(rel.items || []);
      setFoodHandoffs(fh.items || []);
      setTrends(tr.items || []);
      setInvoices(inv.items || []);
      setEvents(ev.items || []);
      setPartnerPrograms(pp.items || []);
      setEntitlements(ent.items || []);
      setDunningCases(dun.items || []);
      setDeliveries(del.items || []);
      setChurnAlerts(churn.items || []);
      setReferrals(refs.items || []);
      setWorldSummary(wsum.counts || null);
      setRegionalPrices(reg.items || []);
      setAddonCatalog(addons.items || []);
      setRetentionOffers(ret.items || []);
      setSettlements(sett.items || []);
      setEfficiencySummary(esum.counts || null);
      setOpsInbox(inbox.items || []);
      setInboxBulkOps(inbox.bulk_operations || []);
      setPromoCodes(promos.items || []);
      setUpgradeSuggestions(upgrades.items || []);
      setAutomationRules(rules.items || []);
      setUsageMeters(meters.items || []);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  const onSeed = async () => {
    if (!canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const data = await apiFetch("/seed", { method: "POST" });
      setOk(`Seed OK: ${JSON.stringify(data.seeded || data)}`);
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const onSyncEcosystem = async () => {
    if (!canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const data = await apiFetch("/sync/ecosystem-full", { method: "POST" });
      setOk(`Ecossistema sincronizado: ${JSON.stringify(data.synced || data)}`);
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const onCreateSubscription = async (e) => {
    e.preventDefault();
    if (!canMutate || !subForm.user_id.trim()) return;
    setLoading(true);
    setErr("");
    try {
      await apiFetch("/subscriptions", {
        method: "POST",
        body: JSON.stringify({
          user_id: subForm.user_id.trim(),
          plan_type: subForm.plan_type,
          partner_code: subForm.partner_code.trim() || undefined,
          promo_code: subForm.promo_code.trim() || undefined,
        }),
      });
      setOk("Assinatura criada.");
      setSubForm({ user_id: "", plan_type: "PREMIUM", partner_code: "", promo_code: "" });
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const onInboxAction = async (item, action = "primary") => {
    if (!canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const notes =
        action === "apply_upgrade" && item.suggested_plan ? String(item.suggested_plan) : undefined;
      await apiFetch("/efficiency/ops-inbox/act", {
        method: "POST",
        body: JSON.stringify({
          kind: String(item.kind),
          id: String(item.id),
          action,
          notes,
        }),
      });
      setOk(`Ação ${action} em ${item.kind} concluída.`);
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const onInboxBulk = async (operation) => {
    if (!canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const data = await apiFetch("/efficiency/ops-inbox/bulk", {
        method: "POST",
        body: JSON.stringify({ operation }),
      });
      setOk(`Bulk: ${data.processed} processado(s).`);
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const onCreatePromo = async (e) => {
    e.preventDefault();
    if (!canMutate || !promoForm.code.trim()) return;
    setLoading(true);
    setErr("");
    try {
      await apiFetch("/efficiency/promo-codes", {
        method: "POST",
        body: JSON.stringify({
          code: promoForm.code.trim(),
          description: promoForm.description.trim() || undefined,
          discount_pct: promoForm.discount_pct,
          eligible_plans: promoForm.eligible_plans.split(",").map((p) => p.trim()).filter(Boolean),
          max_redemptions: promoForm.max_redemptions,
        }),
      });
      setOk(`Cupom ${promoForm.code} criado.`);
      setShowPromoForm(false);
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const onCreateRule = async (e) => {
    e.preventDefault();
    if (!canMutate || !ruleForm.rule_code.trim()) return;
    setLoading(true);
    setErr("");
    try {
      await apiFetch("/efficiency/automation-rules", {
        method: "POST",
        body: JSON.stringify({
          rule_code: ruleForm.rule_code.trim(),
          name: ruleForm.name.trim(),
          trigger_event: ruleForm.trigger_event,
          action_type: ruleForm.action_type,
          config_json: {},
        }),
      });
      setOk("Regra criada.");
      setShowRuleForm(false);
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const onRotateKey = async () => {
    if (!canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const data = await apiFetch(`/api-keys/${encodeURIComponent(webhookPartner)}/rotate`, { method: "POST" });
      setLastApiKey(data.api_key || "");
      setOk("API key rotacionada — copie agora.");
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const onUpsertWebhook = async (e) => {
    e.preventDefault();
    if (!canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const data = await apiFetch(`/webhooks/${encodeURIComponent(webhookPartner)}`, {
        method: "PUT",
        body: JSON.stringify({
          url: webhookUrl,
          events: ["subscription.created", "subscription.renewed", "subscription.cancelled", "subscription.past_due"],
        }),
      });
      if (data.secret) setOk(`Webhook salvo. Secret: ${String(data.secret).slice(0, 16)}…`);
      else setOk("Webhook salvo.");
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const overviewKpis = [
    ["MRR", formatBrl(summary?.mrr_cents ?? 0)],
    ["Assinaturas ativas", summary?.active_subscriptions ?? "—"],
    ["Em trial", summary?.trialing_subscriptions ?? "—"],
    ["Past due", summary?.past_due_subscriptions ?? "—"],
    ["Planos ativos", summary?.active_plans ?? plans.filter((p) => p.is_active).length],
    ["Parceiros webhook", webhooks.length],
    ["Entitlements", entitlements.length],
    ["Alertas churn", churnAlerts.length],
    ["Ofertas retenção", retentionOffers.length],
    ["Preços regionais", regionalPrices.length],
    ["Relações rede", relations.length],
    ["Food handoffs", foodHandoffs.length],
  ];

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Assinaturas (Subscriptions)" versionLabel={PAGE_VERSION} />
        <p style={mutedTextStyle}>
          Planos B2C, benefícios, faturamento, ecossistema mundial (InPost, DHL, Magalu, Mercado Livre, Amazon…) e
          integrações B2B. API <code style={{ color: "#93c5fd" }}>{API}</code>
        </p>
        {catalog ? (
          <p style={mutedTextStyle}>
            Ecossistema: {(catalog.priority_player_codes || []).length} players prioritários ·{" "}
            {catalog.relations_total ?? relations.length} relações · seed + sync para atualizar base mundial.
          </p>
        ) : null}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
          <a href={V1_SUBSCRIPTIONS_HUB} style={crossShortcutLinkStyle} title="Abrir hub v1">
            Hub v1 (Tailwind)
          </a>
          <span style={{ ...mutedTextStyle, margin: 0, fontSize: 12, alignSelf: "center" }}>
            Contrato API: docs/SUBSCRIPTIONS_API_CONTRACT.md
          </span>
        </div>

        {!canMutate ? (
          <p style={{ ...criticalBannerStyle, marginTop: 12 }}>
            Modo leitura — ações de escrita (seed, sync, webhooks) exigem perfil <strong>admin_operacao</strong>.
          </p>
        ) : null}
        {err ? <p style={{ ...criticalBannerStyle, marginTop: 12 }}>{err}</p> : null}
        {ok ? <p style={{ ...okBannerStyle, marginTop: 12 }}>{ok}</p> : null}
        {lastApiKey ? <p style={{ ...apiKeyBannerStyle, marginTop: 12 }}>Nova API key: {lastApiKey}</p> : null}
        {loading ? (
          <p style={{ ...mutedTextStyle, marginTop: 8, color: "#93c5fd" }}>Carregando dados…</p>
        ) : null}

        <div style={{ ...opsSanityCardStyle, marginTop: 14 }}>
          <div style={{ fontSize: 12, color: "#94a3b8", fontWeight: 600 }}>Navegação por área</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {TAB_GROUPS.map((g) => (
              <button
                key={g.id}
                type="button"
                style={{
                  ...tabButtonStyle(tabGroup === g.id),
                  fontSize: 12,
                }}
                onClick={() => {
                  setTabGroup(g.id);
                  const first = g.tabs[0]?.id;
                  if (first) setTabUrl(first);
                }}
              >
                {g.label}
              </button>
            ))}
          </div>
          <div style={{ ...toolbarStyle, marginTop: 4 }}>
            {activeGroup.tabs.map((t) => (
              <button key={t.id} type="button" style={tabButtonStyle(tab === t.id)} onClick={() => setTabUrl(t.id)}>
                {t.label}
              </button>
            ))}
            <button type="button" style={buttonGhostStyle} onClick={() => void load()} disabled={loading}>
              Atualizar
            </button>
            {canMutate ? (
              <>
                <button type="button" style={buttonPrimaryStyle} onClick={() => void onSeed()} disabled={loading}>
                  Seed demo
                </button>
                <button type="button" style={buttonGhostStyle} onClick={() => void onSyncEcosystem()} disabled={loading}>
                  Sync ecossistema
                </button>
              </>
            ) : null}
          </div>
        </div>

        {tab === "overview" ? (
          <>
            <SectionTitle hint="Indicadores consolidados do domínio de assinaturas.">Visão geral</SectionTitle>
            <KpiGrid items={overviewKpis} />
          </>
        ) : null}

        {tab === "analytics" ? (
          <div style={{ marginTop: 16 }}>
            <SectionTitle hint="MRR e assinantes por plano nos últimos meses.">Tendências MRR</SectionTitle>
            <div style={{ overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["Mês", "Plano", "Assinantes", "MRR"].map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {trends.length === 0 ? (
                    <EmptyRow colSpan={4} message="Sem tendências — execute Seed demo." />
                  ) : (
                    trends.map((row, i) => (
                      <tr key={`${row.month_ref}-${row.plan_type}-${i}`}>
                        <td style={tdStyle}>{row.month_ref}</td>
                        <td style={tdStyle}>{row.plan_type}</td>
                        <td style={tdStyle}>{row.active_subscribers ?? "—"}</td>
                        <td style={tdStyle}>{formatBrl(row.mrr_cents)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        {tab === "ecosystem" ? (
          <div style={{ marginTop: 16, display: "grid", gap: 12 }}>
            <SectionTitle hint="Players locker, marketplaces, carriers e food delivery por tier de plano.">
              Ecossistema mundial
            </SectionTitle>
            <div style={cardStyle}>
              <strong style={{ color: "#e2e8f0" }}>Players prioritários</strong>
              <p style={{ ...mutedTextStyle, marginTop: 8 }}>
                {(priorityPlayers.length
                  ? priorityPlayers.map((p) => p.name || p.code)
                  : catalog?.priority_player_codes || []
                ).join(" · ") || "—"}
              </p>
            </div>
            {catalog ? (
              <details style={cardStyle}>
                <summary style={{ cursor: "pointer", color: "#cbd5e1", fontWeight: 600 }}>Mapa tier → players</summary>
                <pre style={{ fontSize: 11, overflow: "auto", marginTop: 12, color: "#94a3b8" }}>
                  {JSON.stringify(catalog.tier_player_map, null, 2)}
                </pre>
              </details>
            ) : (
              <p style={mutedTextStyle}>Catálogo indisponível — Sync ecossistema.</p>
            )}
          </div>
        ) : null}

        {tab === "plans" ? (
          <div style={{ marginTop: 16 }}>
            <SectionTitle>Planos de assinatura</SectionTitle>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["Código", "Nome", "Mensal", "Benefícios", "Ativo"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {plans.length === 0 ? (
                  <EmptyRow colSpan={5} message="Nenhum plano cadastrado." />
                ) : (
                  plans.map((p) => (
                    <tr key={p.id}>
                      <td style={{ ...tdStyle, fontFamily: "monospace", color: "#93c5fd" }}>{p.code}</td>
                      <td style={tdStyle}>{p.name}</td>
                      <td style={tdStyle}>{formatBrl(p.monthly_fee_cents)}</td>
                      <td style={{ ...tdStyle, fontSize: 11 }}>
                        {[p.free_shipping && "frete", p.priority_shelf && "prateleira", p.exclusive_deals && "ofertas"]
                          .filter(Boolean)
                          .join(" · ") || "—"}
                      </td>
                      <td style={tdStyle}>{p.is_active ? "Sim" : "Não"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "subscriptions" ? (
          <div style={{ marginTop: 16, display: "grid", gap: 16 }}>
            <SectionTitle hint="Filtre por status e crie assinaturas de demonstração.">Assinaturas ativas</SectionTitle>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                Status
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="">Todos</option>
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="TRIALING">TRIALING</option>
                  <option value="PAST_DUE">PAST_DUE</option>
                  <option value="CANCELLED">CANCELLED</option>
                </select>
              </label>
            </div>
            {canMutate ? (
              <form onSubmit={onCreateSubscription} style={{ ...cardStyle, display: "grid", gap: 10 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#cbd5e1" }}>Nova assinatura</div>
                <div style={healthLocalFilterRowStyle}>
                  <label style={healthLocalFilterFieldStyle}>
                    user_id
                    <input
                      value={subForm.user_id}
                      onChange={(e) => setSubForm((f) => ({ ...f, user_id: e.target.value }))}
                      style={healthLocalFilterInputStyle}
                      placeholder="uuid do usuário"
                    />
                  </label>
                  <label style={healthLocalFilterFieldStyle}>
                    Plano
                    <select
                      value={subForm.plan_type}
                      onChange={(e) => setSubForm((f) => ({ ...f, plan_type: e.target.value }))}
                      style={healthLocalFilterInputStyle}
                    >
                      {["BASIC", "PREMIUM", "PRO", "ENTERPRISE"].map((c) => (
                        <option key={c} value={c}>
                          {c}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label style={healthLocalFilterFieldStyle}>
                    partner_code
                    <input
                      value={subForm.partner_code}
                      onChange={(e) => setSubForm((f) => ({ ...f, partner_code: e.target.value }))}
                      style={healthLocalFilterInputStyle}
                      placeholder="magalu (opcional)"
                    />
                  </label>
                  <label style={healthLocalFilterFieldStyle}>
                    cupom
                    <input
                      value={subForm.promo_code}
                      onChange={(e) => setSubForm((f) => ({ ...f, promo_code: e.target.value.toUpperCase() }))}
                      style={healthLocalFilterInputStyle}
                      placeholder="WELCOME20"
                    />
                  </label>
                </div>
                <button type="submit" style={buttonPrimaryStyle} disabled={loading}>
                  Criar assinatura
                </button>
              </form>
            ) : null}
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["Usuário", "Plano", "Status", "Mensal", "Parceiro", "Período"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {subscriptions.length === 0 ? (
                  <EmptyRow colSpan={6} message="Nenhuma assinatura para o filtro atual." />
                ) : (
                  subscriptions.map((s) => (
                    <tr key={s.id}>
                      <td style={tdStyle} title={s.id}>
                        {String(s.user_id || "").slice(0, 12)}…
                      </td>
                      <td style={tdStyle}>{s.plan_type}</td>
                      <td style={tdStyle}>
                        <span style={statusPill(s.status)}>{s.status}</span>
                      </td>
                      <td style={tdStyle}>{formatBrl(s.monthly_fee_cents)}</td>
                      <td style={tdStyle}>{s.partner_code || "—"}</td>
                      <td style={{ ...tdStyle, fontSize: 11 }}>
                        {s.current_period_end ? String(s.current_period_end).slice(0, 10) : "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "benefits" ? (
          <div style={{ marginTop: 16 }}>
            <SectionTitle>Uso de benefícios por assinatura</SectionTitle>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["Assinatura", "Mês", "Benefício", "Uso", "Limite"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {benefits.length === 0 ? (
                  <EmptyRow colSpan={5} message="Sem uso de benefícios registrado." />
                ) : (
                  benefits.map((b) => (
                    <tr key={b.id}>
                      <td style={{ ...tdStyle, fontFamily: "monospace", fontSize: 11 }}>{String(b.subscription_id).slice(0, 8)}…</td>
                      <td style={tdStyle}>{b.usage_month}</td>
                      <td style={tdStyle}>{b.benefit_type}</td>
                      <td style={tdStyle}>{b.usage_count}</td>
                      <td style={tdStyle}>{b.usage_limit ?? "∞"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "billing" ? (
          <div style={{ marginTop: 16 }}>
            <SectionTitle>Faturas (subscription_invoices)</SectionTitle>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["Status", "Valor", "Período", "Pago em"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {invoices.length === 0 ? (
                  <EmptyRow colSpan={4} message="Nenhuma fatura." />
                ) : (
                  invoices.map((inv) => (
                    <tr key={inv.id}>
                      <td style={tdStyle}>{inv.status}</td>
                      <td style={tdStyle}>{formatBrl(inv.amount_cents)}</td>
                      <td style={{ ...tdStyle, fontSize: 11 }}>
                        {inv.period_start ? String(inv.period_start).slice(0, 10) : "—"} →{" "}
                        {inv.period_end ? String(inv.period_end).slice(0, 10) : "—"}
                      </td>
                      <td style={tdStyle}>{inv.paid_at ? String(inv.paid_at).slice(0, 10) : "—"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "events" ? (
          <div style={{ marginTop: 16 }}>
            <SectionTitle>Eventos de lifecycle</SectionTitle>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["Tipo", "Assinatura", "Quando"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {events.length === 0 ? (
                  <EmptyRow colSpan={3} message="Nenhum evento." />
                ) : (
                  events.map((ev) => (
                    <tr key={ev.id}>
                      <td style={tdStyle}>{ev.event_type}</td>
                      <td style={tdStyle}>{String(ev.subscription_id).slice(0, 8)}…</td>
                      <td style={tdStyle}>{ev.created_at ? String(ev.created_at).slice(0, 19) : "—"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "partners" ? (
          <div style={{ marginTop: 16 }}>
            <SectionTitle>Programas parceiros B2B</SectionTitle>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["Código", "Nome", "Tipo", "Plano default", "KYB"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {partnerPrograms.length === 0 ? (
                  <EmptyRow colSpan={5} message="Nenhum programa parceiro." />
                ) : (
                  partnerPrograms.map((p) => (
                    <tr key={p.id}>
                      <td style={tdStyle}>{p.partner_code}</td>
                      <td style={tdStyle}>{p.partner_name}</td>
                      <td style={tdStyle}>{p.partner_type}</td>
                      <td style={tdStyle}>{p.default_plan_code}</td>
                      <td style={tdStyle}>{p.kyb_status || "—"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "entitlements" ? (
          <div style={{ marginTop: 16 }}>
            <SectionTitle>Entitlements plano × player</SectionTitle>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["Plano", "Player", "Tipo", "Prioridade"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {entitlements.length === 0 ? (
                  <EmptyRow colSpan={4} message="Sem entitlements — Sync ecossistema." />
                ) : (
                  entitlements.slice(0, 80).map((e) => (
                    <tr key={e.id}>
                      <td style={tdStyle}>{e.plan_code}</td>
                      <td style={tdStyle}>{e.player_name}</td>
                      <td style={tdStyle}>{e.player_type || "—"}</td>
                      <td style={tdStyle}>{e.priority_level ?? 0}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "dunning" ? (
          <div style={{ marginTop: 16 }}>
            <SectionTitle>Casos de dunning</SectionTitle>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["Estágio", "Status", "Valor devido", "Aberto"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dunningCases.length === 0 ? (
                  <EmptyRow colSpan={4} message="Nenhum caso de dunning aberto." />
                ) : (
                  dunningCases.map((d) => (
                    <tr key={d.id}>
                      <td style={tdStyle}>{d.stage}</td>
                      <td style={tdStyle}>{d.status}</td>
                      <td style={tdStyle}>{formatBrl(d.amount_due_cents)}</td>
                      <td style={tdStyle}>{d.opened_at ? String(d.opened_at).slice(0, 10) : "—"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "integrations" ? (
          <div style={{ marginTop: 16, display: "grid", gap: 16 }}>
            <SectionTitle hint="Configure webhooks outbound e rotacione API keys de parceiros.">
              Webhooks & API keys
            </SectionTitle>
            <form onSubmit={onUpsertWebhook} style={{ ...cardStyle, display: "grid", gap: 10, maxWidth: 560 }}>
              <div style={healthLocalFilterRowStyle}>
                <label style={healthLocalFilterFieldStyle}>
                  partner_code
                  <input
                    value={webhookPartner}
                    onChange={(e) => setWebhookPartner(e.target.value)}
                    style={healthLocalFilterInputStyle}
                  />
                </label>
                <label style={{ ...healthLocalFilterFieldStyle, gridColumn: "1 / -1" }}>
                  URL HTTPS
                  <input
                    value={webhookUrl}
                    onChange={(e) => setWebhookUrl(e.target.value)}
                    style={healthLocalFilterInputStyle}
                  />
                </label>
              </div>
              {canMutate ? (
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <button type="submit" style={buttonPrimaryStyle} disabled={loading}>
                    Salvar webhook
                  </button>
                  <button type="button" style={buttonGhostStyle} onClick={() => void onRotateKey()} disabled={loading}>
                    Rotacionar API key
                  </button>
                </div>
              ) : null}
            </form>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["Parceiro", "URL", "Ativo", "Prefix key"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {webhooks.length === 0 ? (
                  <EmptyRow colSpan={4} message="Nenhum webhook configurado." />
                ) : (
                  webhooks.map((wh) => (
                    <tr key={wh.id}>
                      <td style={tdStyle}>{wh.partner_code}</td>
                      <td style={{ ...tdStyle, fontSize: 11, maxWidth: 220, wordBreak: "break-all" }}>{wh.url}</td>
                      <td style={tdStyle}>{wh.active ? "Sim" : "Não"}</td>
                      <td style={tdStyle}>
                        {(apiKeys.find((k) => k.partner_code === wh.partner_code) || {}).key_prefix || "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "deliveries" ? (
          <div style={{ marginTop: 16 }}>
            <SectionTitle>Log de entregas webhook</SectionTitle>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["Evento", "HTTP", "Tentativa", "Quando"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {deliveries.length === 0 ? (
                  <EmptyRow colSpan={4} message="Nenhuma entrega registrada." />
                ) : (
                  deliveries.map((d) => (
                    <tr key={d.id}>
                      <td style={tdStyle}>{d.event_type}</td>
                      <td style={tdStyle}>{d.http_status ?? "—"}</td>
                      <td style={tdStyle}>{d.attempt_no}</td>
                      <td style={tdStyle}>{d.delivered_at ? String(d.delivered_at).slice(0, 19) : "—"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "relations" ? (
          <div style={{ marginTop: 16 }}>
            <SectionTitle>Relações entre players (locker, marketplace, food)</SectionTitle>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["De", "Para", "Tipo", "Modo"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {relations.length === 0 ? (
                  <EmptyRow colSpan={4} message="Sem relações — Sync ecossistema." />
                ) : (
                  relations.slice(0, 60).map((r) => (
                    <tr key={r.id}>
                      <td style={tdStyle}>{r.from_player_code}</td>
                      <td style={tdStyle}>{r.to_player_code}</td>
                      <td style={tdStyle}>{r.relation_type}</td>
                      <td style={tdStyle}>{r.integration_mode || "—"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "food_delivery" ? (
          <div style={{ marginTop: 16 }}>
            <SectionTitle>Handoffs food delivery → locker/PUDO</SectionTitle>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["Food platform", "Pickup player", "Tipo", "SLA min"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {foodHandoffs.length === 0 ? (
                  <EmptyRow colSpan={4} message="Sem handoffs — Sync ecossistema." />
                ) : (
                  foodHandoffs.map((h) => (
                    <tr key={h.id}>
                      <td style={tdStyle}>{h.food_platform_code}</td>
                      <td style={tdStyle}>{h.pickup_player_code}</td>
                      <td style={tdStyle}>{h.handoff_type}</td>
                      <td style={tdStyle}>{h.sla_minutes ?? "—"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "premium" ? (
          <div style={{ marginTop: 16, display: "grid", gap: 12 }}>
            <SectionTitle hint="Health score, referrals, gifts, loyalty e fila de renovação.">Premium & growth</SectionTitle>
            <div style={toolbarStyle}>
              {canMutate ? (
                <>
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    disabled={loading}
                    onClick={() =>
                      void apiFetch("/premium/seed", { method: "POST" })
                        .then((d) => setOk(`Premium: ${JSON.stringify(d.seeded)}`))
                        .catch((e) => setErr(String(e.message || e)))
                    }
                  >
                    Seed premium
                  </button>
                  <button
                    type="button"
                    style={buttonGhostStyle}
                    disabled={loading}
                    onClick={() =>
                      void apiFetch("/health/compute-all", { method: "POST" })
                        .then((d) => setOk(`Health: ${d.computed} assinaturas`))
                        .catch((e) => setErr(String(e.message || e)))
                    }
                  >
                    Calcular health
                  </button>
                  <button
                    type="button"
                    style={buttonGhostStyle}
                    disabled={loading}
                    onClick={() =>
                      void apiFetch("/renewals/run-due", { method: "POST" })
                        .then((d) => setOk(`Renovações: ${d.processed}`))
                        .catch((e) => setErr(String(e.message || e)))
                    }
                  >
                    Processar renovações
                  </button>
                </>
              ) : null}
            </div>
            <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))" }}>
              <div style={cardStyle}>
                <strong style={{ color: "#e2e8f0" }}>Referrals ({referrals.length})</strong>
                <ul style={{ fontSize: 12, marginTop: 8, color: "#94a3b8", paddingLeft: 18 }}>
                  {referrals.slice(0, 12).map((r) => (
                    <li key={r.id}>
                      {r.referral_code} · {r.status} · {formatBrl(r.reward_cents)}
                    </li>
                  ))}
                </ul>
              </div>
              <div style={cardStyle}>
                <strong style={{ color: "#e2e8f0" }}>Churn alerts ({churnAlerts.length})</strong>
                <ul style={{ fontSize: 12, marginTop: 8, color: "#94a3b8", paddingLeft: 18 }}>
                  {churnAlerts.slice(0, 12).map((a) => (
                    <li key={a.id}>
                      [{a.severity}] {a.alert_type}: {a.message}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ) : null}

        {tab === "global" ? (
          <div style={{ marginTop: 16, display: "grid", gap: 12 }}>
            <SectionTitle hint="Preços multi-região, add-ons, SLA, settlements e LGPD.">Global & compliance</SectionTitle>
            <div style={toolbarStyle}>
              {canMutate ? (
                <button
                  type="button"
                  style={buttonPrimaryStyle}
                  disabled={loading}
                  onClick={() =>
                    void apiFetch("/world/seed", { method: "POST" })
                      .then((d) => setOk(`Global: ${JSON.stringify(d.seeded)}`))
                      .catch((e) => setErr(String(e.message || e)))
                  }
                >
                  Seed global
                </button>
              ) : null}
            </div>
            {worldSummary ? (
              <KpiGrid
                items={Object.entries(worldSummary).map(([k, v]) => [
                  k.replace(/_/g, " "),
                  String(v),
                ])}
              />
            ) : null}
            <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))" }}>
              <div style={cardStyle}>
                <strong style={{ color: "#e2e8f0" }}>Preços regionais</strong>
                <ul style={{ fontSize: 11, marginTop: 8, color: "#94a3b8", paddingLeft: 18, maxHeight: 200, overflow: "auto" }}>
                  {regionalPrices.slice(0, 20).map((r) => (
                    <li key={`${r.plan_code}-${r.region_code}`}>
                      {r.plan_code} · {r.region_code} · {r.currency} · {formatBrl(r.monthly_fee_cents)}
                    </li>
                  ))}
                </ul>
              </div>
              <div style={cardStyle}>
                <strong style={{ color: "#e2e8f0" }}>Add-ons ({addonCatalog.length})</strong>
                <ul style={{ fontSize: 11, marginTop: 8, color: "#94a3b8", paddingLeft: 18 }}>
                  {addonCatalog.map((a) => (
                    <li key={a.code}>
                      {a.name} · {formatBrl(a.monthly_fee_cents)}
                    </li>
                  ))}
                </ul>
              </div>
              <div style={cardStyle}>
                <strong style={{ color: "#e2e8f0" }}>Settlements parceiros</strong>
                <ul style={{ fontSize: 11, marginTop: 8, color: "#94a3b8", paddingLeft: 18 }}>
                  {settlements.map((s) => (
                    <li key={s.id}>
                      {s.partner_code} · {s.period_month} · {formatBrl(s.net_cents)} ({s.status})
                    </li>
                  ))}
                </ul>
              </div>
              <div style={cardStyle}>
                <strong style={{ color: "#e2e8f0" }}>Ofertas retenção</strong>
                <ul style={{ fontSize: 11, marginTop: 8, color: "#94a3b8", paddingLeft: 18 }}>
                  {retentionOffers.slice(0, 10).map((o) => (
                    <li key={o.id}>
                      {o.offer_code} · {o.discount_pct}% · {o.status}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ) : null}

        {tab === "efficiency" ? (
          <div style={{ marginTop: 16, display: "grid", gap: 12 }}>
            <SectionTitle hint="Inbox OPS unificado, cupons, upgrade matrix e automações.">
              Eficiência & Smart OPS
            </SectionTitle>
            <div style={toolbarStyle}>
              {canMutate ? (
                <button
                  type="button"
                  style={buttonPrimaryStyle}
                  disabled={loading}
                  onClick={() =>
                    void apiFetch("/efficiency/seed", { method: "POST" })
                      .then((d) => setOk(`Eficiência: ${JSON.stringify(d.seeded)}`))
                      .catch((e) => setErr(String(e.message || e)))
                  }
                >
                  Seed eficiência
                </button>
              ) : null}
            </div>
            {efficiencySummary ? (
              <KpiGrid
                items={Object.entries(efficiencySummary).map(([k, v]) => [k.replace(/_/g, " "), String(v)])}
              />
            ) : null}
            <div style={toolbarStyle}>
              {canMutate ? (
                <>
                  <button type="button" style={buttonPrimaryStyle} onClick={() => setShowPromoForm((v) => !v)}>
                    {showPromoForm ? "Fechar cupom" : "Novo cupom"}
                  </button>
                  <button type="button" style={buttonPrimaryStyle} onClick={() => setShowRuleForm((v) => !v)}>
                    {showRuleForm ? "Fechar regra" : "Nova automação"}
                  </button>
                </>
              ) : null}
            </div>
            {showPromoForm && canMutate ? (
              <form onSubmit={onCreatePromo} style={{ ...cardStyle, display: "grid", gap: 8 }}>
                <input
                  required
                  placeholder="Código"
                  value={promoForm.code}
                  onChange={(e) => setPromoForm((f) => ({ ...f, code: e.target.value.toUpperCase() }))}
                  style={healthLocalFilterInputStyle}
                />
                <input
                  placeholder="Descrição"
                  value={promoForm.description}
                  onChange={(e) => setPromoForm((f) => ({ ...f, description: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
                <button type="submit" style={buttonPrimaryStyle} disabled={loading}>
                  Criar cupom
                </button>
              </form>
            ) : null}
            {showRuleForm && canMutate ? (
              <form onSubmit={onCreateRule} style={{ ...cardStyle, display: "grid", gap: 8 }}>
                <input
                  required
                  placeholder="rule_code"
                  value={ruleForm.rule_code}
                  onChange={(e) => setRuleForm((f) => ({ ...f, rule_code: e.target.value.toUpperCase() }))}
                  style={healthLocalFilterInputStyle}
                />
                <input
                  required
                  placeholder="Nome"
                  value={ruleForm.name}
                  onChange={(e) => setRuleForm((f) => ({ ...f, name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
                <button type="submit" style={buttonPrimaryStyle} disabled={loading}>
                  Criar regra
                </button>
              </form>
            ) : null}
            <div style={cardStyle}>
              <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 8, marginBottom: 8 }}>
                <strong style={{ color: "#e2e8f0" }}>OPS Inbox ({opsInbox.length})</strong>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {inboxBulkOps.map((op) => (
                    <button
                      key={op.operation}
                      type="button"
                      disabled={loading || !canMutate}
                      style={{ ...buttonPrimaryStyle, fontSize: 10, padding: "2px 6px" }}
                      onClick={() => void onInboxBulk(op.operation)}
                    >
                      {op.label}
                    </button>
                  ))}
                </div>
              </div>
              <ul style={{ fontSize: 11, marginTop: 8, color: "#94a3b8", paddingLeft: 0, listStyle: "none", maxHeight: 220, overflow: "auto" }}>
                {opsInbox.slice(0, 25).map((item, i) => {
                  const actions = item.actions || [];
                  return (
                    <li
                      key={`${item.kind}-${item.id || i}`}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: 8,
                        padding: "6px 0",
                        borderBottom: "1px solid #1e293b",
                      }}
                    >
                      <span>
                        [{item.kind}] {item.title || "—"}
                      </span>
                      {canMutate ? (
                        <span style={{ display: "flex", gap: 4 }}>
                          {actions.map((a) => (
                            <button
                              key={a.action}
                              type="button"
                              style={{ ...buttonPrimaryStyle, fontSize: 10, padding: "2px 8px" }}
                              disabled={loading}
                              onClick={() => void onInboxAction(item, a.action)}
                            >
                              {a.label}
                            </button>
                          ))}
                        </span>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            </div>
            <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))" }}>
              <div style={cardStyle}>
                <strong style={{ color: "#e2e8f0" }}>Cupons ({promoCodes.length})</strong>
                <ul style={{ fontSize: 11, marginTop: 8, color: "#94a3b8", paddingLeft: 18 }}>
                  {promoCodes.map((p) => (
                    <li key={p.code}>
                      {p.code} · {p.discount_pct}% · {p.description}
                    </li>
                  ))}
                </ul>
              </div>
              <div style={cardStyle}>
                <strong style={{ color: "#e2e8f0" }}>Upgrade matrix ({upgradeSuggestions.length})</strong>
                <ul style={{ fontSize: 11, marginTop: 8, color: "#94a3b8", paddingLeft: 18 }}>
                  {upgradeSuggestions.map((u, i) => (
                    <li key={u.subscription_id || i}>
                      {u.current_plan} → {u.suggested_plan} · uso {u.usage_pct}%
                    </li>
                  ))}
                </ul>
              </div>
              <div style={cardStyle}>
                <strong style={{ color: "#e2e8f0" }}>Automações ({automationRules.length})</strong>
                <ul style={{ fontSize: 11, marginTop: 8, color: "#94a3b8", paddingLeft: 18 }}>
                  {automationRules.map((r) => (
                    <li key={r.rule_code}>
                      {r.name} · {r.trigger_event} → {r.action_type}
                    </li>
                  ))}
                </ul>
              </div>
              <div style={cardStyle}>
                <strong style={{ color: "#e2e8f0" }}>Medidores ({usageMeters.length})</strong>
                <ul style={{ fontSize: 11, marginTop: 8, color: "#94a3b8", paddingLeft: 18 }}>
                  {usageMeters.slice(0, 15).map((m, i) => (
                    <li key={m.id || i}>
                      {m.meter_code} · {m.period_month} · qty {m.quantity}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ) : null}
      </section>
    </div>
  );
}

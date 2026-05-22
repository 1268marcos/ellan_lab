
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
  healthLocalFilterFieldStyle,
  healthLocalFilterInputStyle,
  healthLocalFilterRowStyle,
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

const BASE = import.meta.env.VITE_PARTNER_ADMIN_BASE_URL || "/api/pa";
const API = `${BASE}/v1/partner-admin`;
const PAGE_VERSION = "ops/partners/admin v0.3";

const TAB_KEYS = [
  "overview",
  "onboarding",
  "ecommerce",
  "logistics",
  "integrations",
  "webhook_monitor",
  "integration_health",
  "outbox",
  "contacts",
  "settlements",
  "service_areas",
  "billing",
  "invoices",
  "credits",
  "holds",
  "commission",
  "sla",
  "status",
  "stores",
  "ecosystem",
  "global_ops",
  "capability_webhooks",
];

const TABS = [
  { key: "overview", label: "Visão 360" },
  { key: "onboarding", label: "Onboarding" },
  { key: "ecommerce", label: "E-commerce" },
  { key: "logistics", label: "Logística" },
  { key: "integrations", label: "Webhook / API" },
  { key: "webhook_monitor", label: "Entregas webhook" },
  { key: "integration_health", label: "Saúde integração" },
  { key: "outbox", label: "Outbox" },
  { key: "contacts", label: "Contatos" },
  { key: "settlements", label: "Settlements" },
  { key: "service_areas", label: "Service areas" },
  { key: "billing", label: "Billing" },
  { key: "invoices", label: "NF B2B" },
  { key: "credits", label: "Créditos" },
  { key: "holds", label: "Retenções" },
  { key: "commission", label: "Comissão" },
  { key: "sla", label: "SLA" },
  { key: "status", label: "Histórico status" },
  { key: "stores", label: "Lojas C&C" },
  { key: "ecosystem", label: "Redes mundiais" },
  { key: "global_ops", label: "Global OPS" },
  { key: "capability_webhooks", label: "Webhooks DLQ" },
];

function parseError(payload, fallback = "Falha na API partner-admin.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  return fallback;
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao (${endpoint}). Verifique proxy ${BASE} (porta 8016).`;
  }
  return raw;
}

async function apiFetch(path, { headers, method = "GET", body } = {}) {
  const r = await fetch(`${API}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(parseError(j));
  return j;
}

function JsonBlock({ title, data }) {
  return (
    <section style={opsSanityCardStyle}>
      <div style={summary24hHeaderStyle}>
        <h3 style={{ margin: 0, fontSize: 14 }}>{title}</h3>
      </div>
      <pre
        style={{
          margin: 0,
          padding: 12,
          background: "#020617",
          border: "1px solid #334155",
          borderRadius: 8,
          fontSize: 11,
          overflow: "auto",
          maxHeight: 360,
          color: "#e2e8f0",
        }}
      >
        {JSON.stringify(data, null, 2)}
      </pre>
    </section>
  );
}

function KpiGrid({ items }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
        gap: 10,
      }}
    >
      {items.map(([label, value]) => (
        <div
          key={label}
          style={{
            padding: 10,
            borderRadius: 8,
            border: "1px solid #334155",
            background: "#0b1220",
          }}
        >
          <div style={{ fontSize: 11, color: "#94a3b8" }}>{label}</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>{value}</div>
        </div>
      ))}
    </div>
  );
}

export default function OpsPartnersAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [searchParams, setSearchParams] = useSearchParams();
  const urlTab = searchParams.get("tab") || "overview";
  const [tab, setTab] = useState(TAB_KEYS.includes(urlTab) ? urlTab : "overview");

  const [ecItems, setEcItems] = useState([]);
  const [lgItems, setLgItems] = useState([]);
  const [form, setForm] = useState({ name: "", code: "" });
  const [selectedId, setSelectedId] = useState("partner_demo_001");
  const [partnerType, setPartnerType] = useState("ECOMMERCE");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [lastApiKey, setLastApiKey] = useState("");
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contacts, setContacts] = useState([]);
  const [p360, setP360] = useState(null);
  const [onboarding, setOnboarding] = useState([]);
  const [onboardingPct, setOnboardingPct] = useState(0);
  const [settlements, setSettlements] = useState([]);
  const [performance, setPerformance] = useState([]);
  const [serviceAreas, setServiceAreas] = useState([]);
  const [billingPlans, setBillingPlans] = useState([]);
  const [billingCycles, setBillingCycles] = useState([]);
  const [lineItems, setLineItems] = useState([]);
  const [webhookDeliveries, setWebhookDeliveries] = useState([]);
  const [integrationHealth, setIntegrationHealth] = useState([]);
  const [outbox, setOutbox] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [creditNotes, setCreditNotes] = useState([]);
  const [paymentHolds, setPaymentHolds] = useState([]);
  const [commissions, setCommissions] = useState([]);
  const [slaItems, setSlaItems] = useState([]);
  const [statusHistory, setStatusHistory] = useState([]);
  const [stores, setStores] = useState([]);
  const [ecosystemPlayers, setEcosystemPlayers] = useState([]);
  const [ecosystemLinks, setEcosystemLinks] = useState([]);
  const [ecoPriorityOnly, setEcoPriorityOnly] = useState(true);
  const [globalOpsSummary, setGlobalOpsSummary] = useState(null);
  const [globalCorridors, setGlobalCorridors] = useState([]);
  const [corridorSla, setCorridorSla] = useState([]);
  const [deadLetterDeliveries, setDeadLetterDeliveries] = useState([]);
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

  const partnerOptions = useMemo(() => {
    const ec = ecItems.map((p) => ({ id: p.id, code: p.code, type: "ECOMMERCE" }));
    const lg = lgItems.map((p) => ({ id: p.id, code: p.code, type: "LOGISTICS" }));
    return [...ec, ...lg];
  }, [ecItems, lgItems]);

  const setTabAndUrl = (next) => {
    setTab(next);
    if (next === "overview") {
      setSearchParams({}, { replace: true });
    } else {
      setSearchParams({ tab: next }, { replace: true });
    }
  };

  useEffect(() => {
    const t = searchParams.get("tab") || "overview";
    if (TAB_KEYS.includes(t) && t !== tab) setTab(t);
  }, [searchParams, tab]);

  const loadPartners = useCallback(async () => {
    const ec = await apiFetch("/ecommerce-partners", { headers });
    const lg = await apiFetch("/logistics-partners", { headers });
    setEcItems(ec.partners || []);
    setLgItems(lg.partners || []);
  }, [headers]);

  const loadDomain = useCallback(async () => {
    if (!selectedId || !token) return;
    const pid = encodeURIComponent(selectedId);
    const pt = encodeURIComponent(partnerType);
    const [
      s,
      perf,
      sa,
      bp,
      bc,
      p360j,
      onb,
      wh,
      ih,
      ob,
      inv,
      li,
      cn,
      ph,
      comm,
      sla,
      st,
      cts,
      ecoLinks,
      ecoPlayers,
    ] = await Promise.all([
      apiFetch(`/partners/${pid}/settlements`, { headers }),
      apiFetch(`/partners/${pid}/performance`, { headers }),
      apiFetch(`/partners/${pid}/service-areas`, { headers }),
      apiFetch(`/partners/${pid}/billing-plans`, { headers }),
      apiFetch(`/partners/${pid}/billing-cycles`, { headers }),
      apiFetch(`/partners/${pid}/360?partner_type=${pt}`, { headers }),
      apiFetch(`/partners/${pid}/onboarding?partner_type=${pt}`, { headers }),
      apiFetch(`/partners/${pid}/webhook-deliveries`, { headers }),
      apiFetch(`/partners/${pid}/integration-health`, { headers }),
      apiFetch(`/partners/${pid}/outbox`, { headers }),
      apiFetch(`/partners/${pid}/invoices`, { headers }),
      apiFetch(`/partners/${pid}/billing-line-items?cycle_id=cycle-demo-001`, { headers }),
      apiFetch(`/partners/${pid}/credit-notes`, { headers }),
      apiFetch(`/partners/${pid}/payment-holds`, { headers }),
      apiFetch(`/partners/${pid}/commissions`, { headers }),
      apiFetch(`/partners/${pid}/sla-agreements`, { headers }),
      apiFetch(`/partners/${pid}/status-history`, { headers }),
      apiFetch(`/partners/${pid}/contacts?partner_type=${pt}`, { headers }),
      apiFetch(`/partners/${pid}/ecosystem-links?partner_type=${pt}`, { headers }),
      apiFetch(`/ecosystem/players?priority_only=${ecoPriorityOnly ? "true" : "false"}`, { headers }),
    ]);
    setSettlements(s.items || []);
    setPerformance(perf.items || []);
    setServiceAreas(sa.items || []);
    setBillingPlans(bp.items || []);
    setBillingCycles(bc.items || []);
    setP360(p360j);
    setOnboarding(onb.items || []);
    setOnboardingPct(onb.progress_pct ?? 0);
    setWebhookDeliveries(wh.items || []);
    setIntegrationHealth(ih.items || []);
    setOutbox(ob.items || []);
    setInvoices(inv.items || []);
    setLineItems(li.items || []);
    setCreditNotes(cn.items || []);
    setPaymentHolds(ph.items || []);
    setCommissions(comm.items || []);
    setSlaItems(sla.items || []);
    setStatusHistory(st.items || []);
    setContacts(cts.contacts || []);
    setEcosystemLinks(ecoLinks.items || []);
    setEcosystemPlayers(ecoPlayers.items || []);
  }, [headers, selectedId, partnerType, token, ecoPriorityOnly]);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErr("");
    setOk("");
    try {
      await loadPartners();
      const st = await apiFetch("/partner-stores", { headers });
      setStores(st.items || []);
      await loadDomain();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  }, [headers, loadDomain, loadPartners, token]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (token && selectedId) void loadDomain();
  }, [selectedId, partnerType, loadDomain, token]);

  const onSeed = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      await apiFetch("/seed", { headers, method: "POST" });
      setOk("Seed aplicado.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seed`));
    } finally {
      setLoading(false);
    }
  };

  const onCreate = async () => {
    if (!token || !canMutate) return;
    const path = tab === "logistics" ? "/logistics-partners" : "/ecommerce-partners";
    setLoading(true);
    setErr("");
    try {
      const j = await apiFetch(path, { headers, method: "POST", body: form });
      setOk(`Parceiro ${j.code} criado.`);
      setSelectedId(j.id);
      setPartnerType(tab === "logistics" ? "LOGISTICS" : "ECOMMERCE");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}${path}`));
    } finally {
      setLoading(false);
    }
  };

  const onWebhook = async () => {
    if (!token || !canMutate || !selectedId || !webhookUrl) return;
    setLoading(true);
    setErr("");
    try {
      const pid = encodeURIComponent(selectedId);
      await apiFetch(`/partners/${pid}/webhook?partner_type=${partnerType}`, {
        headers,
        method: "PUT",
        body: {
          url: webhookUrl,
          secret: webhookSecret || undefined,
          events: ["order.created", "order.updated"],
        },
      });
      setOk(`Webhook salvo para ${selectedId}.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/partners/.../webhook`));
    } finally {
      setLoading(false);
    }
  };

  const onRotate = async () => {
    if (!token || !canMutate || !selectedId) return;
    setLoading(true);
    setErr("");
    try {
      const pid = encodeURIComponent(selectedId);
      const j = await apiFetch(`/partners/${pid}/api-keys/rotate?partner_type=${partnerType}`, {
        headers,
        method: "POST",
      });
      setLastApiKey(j.api_key || "");
      setOk(`Nova API key (${j.key_prefix}…). Copie agora.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/partners/.../api-keys/rotate`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateContact = async () => {
    if (!token || !canMutate || !selectedId || !contactName) return;
    setLoading(true);
    try {
      const pid = encodeURIComponent(selectedId);
      await apiFetch(`/partners/${pid}/contacts?partner_type=${partnerType}`, {
        headers,
        method: "POST",
        body: { name: contactName, email: contactEmail || undefined, is_primary: contacts.length === 0 },
      });
      setContactName("");
      setContactEmail("");
      await loadDomain();
      setOk("Contato criado.");
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onGenerateSettlement = async () => {
    if (!token || !canMutate || !selectedId) return;
    setLoading(true);
    try {
      const pid = encodeURIComponent(selectedId);
      await apiFetch(`/partners/${pid}/settlements/generate`, {
        headers,
        method: "POST",
        body: {
          period_start: "2026-05-01",
          period_end: "2026-05-15",
          revenue_share_pct: 0.15,
          fees_cents: 2500,
          total_orders: 5,
          gross_revenue_cents: 50000,
        },
      });
      setOk("Settlement gerado.");
      await loadDomain();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onProbeHealth = async () => {
    if (!token || !selectedId) return;
    setLoading(true);
    try {
      const pid = encodeURIComponent(selectedId);
      await apiFetch(`/partners/${pid}/integration-health/probe?partner_type=${partnerType}`, {
        headers,
        method: "POST",
      });
      setOk("Probe registrado.");
      await loadDomain();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onMarkOnboardingDone = async (milestoneId) => {
    if (!token || !canMutate || !selectedId) return;
    setLoading(true);
    try {
      const pid = encodeURIComponent(selectedId);
      await apiFetch(`/partners/${pid}/onboarding/${encodeURIComponent(milestoneId)}`, {
        headers,
        method: "PATCH",
        body: { status: "DONE", completed_by: "usr-admin-ops" },
      });
      setOk("Marco atualizado.");
      await loadDomain();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const items = partnerType === "ECOMMERCE" ? ecItems : lgItems;

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10, gap: 8 }}>
          <Link to="/ops/access/user-roles" style={crossShortcutLinkStyle}>
            user_roles
          </Link>
          <Link to="/ops/tenants/admin" style={crossShortcutLinkStyle}>
            Tenants
          </Link>
          <Link to="/ops/partners/dashboard" style={crossShortcutLinkStyle}>
            Partners dashboard
          </Link>
        </div>

        <OpsPageTitleHeader
          title="OPS — Parceiros (admin)"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Domínio partner completo — <code style={{ color: "#e2e8f0" }}>{API}</code> — use as abas ou{" "}
          <code style={{ color: "#e2e8f0" }}>?tab=credits</code> na URL.
        </p>

        <section style={opsSanityCardStyle}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
            {TABS.map((t) => (
              <button key={t.key} type="button" style={tabButtonStyle(tab === t.key)} onClick={() => setTabAndUrl(t.key)}>
                {t.label}
              </button>
            ))}
          </div>

          <div style={healthLocalFilterRowStyle}>
            <label style={healthLocalFilterFieldStyle}>
              partner_id
              <select
                value={selectedId}
                onChange={(e) => {
                  const opt = partnerOptions.find((p) => p.id === e.target.value);
                  setSelectedId(e.target.value);
                  if (opt) setPartnerType(opt.type);
                }}
                style={healthLocalFilterInputStyle}
              >
                <option value="">— selecione —</option>
                {partnerOptions.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.code} ({p.type})
                  </option>
                ))}
              </select>
            </label>
            <label style={healthLocalFilterFieldStyle}>
              partner_type
              <select value={partnerType} onChange={(e) => setPartnerType(e.target.value)} style={healthLocalFilterInputStyle}>
                <option value="ECOMMERCE">ECOMMERCE</option>
                <option value="LOGISTICS">LOGISTICS</option>
              </select>
            </label>
          </div>

          <div style={toolbarStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => void load()} disabled={loading || !token}>
              {loading ? "Atualizando..." : "Atualizar"}
            </button>
            {canMutate ? (
              <button type="button" style={buttonGhostStyle} onClick={() => void onSeed()} disabled={loading}>
                Seed
              </button>
            ) : null}
          </div>
        </section>

        {err ? <div style={criticalBannerStyle} role="alert">{err}</div> : null}
        {ok ? <p style={okBannerStyle}>{ok}</p> : null}
        {lastApiKey ? (
          <p style={apiKeyBannerStyle}>
            API key: <code>{lastApiKey}</code>
          </p>
        ) : null}
        {!token ? <p style={summary24hHintStyle}>Faca login com perfil admin_operacao.</p> : null}

        {tab === "overview" && p360 ? (
          <section style={opsSanityCardStyle}>
            <KpiGrid
              items={[
                ["Onboarding %", `${p360.onboarding_progress_pct}%`],
                ["Integração", p360.integration_status],
                ["Settlements draft", String(p360.settlements_draft)],
                ["Outbox pendente", String(p360.pending_outbox)],
                ["Ciclos abertos", String(p360.open_billing_cycles)],
                ["NF pendentes", String(p360.pending_invoices)],
                ["Webhook falhas 24h", String(p360.webhook_failures_24h)],
                ["SLA ativo", p360.sla_active ? "sim" : "não"],
                ["Redes vinculadas", String(p360.ecosystem_links ?? 0)],
                ["Players prioritários", String(p360.ecosystem_priority_links ?? 0)],
              ]}
            />
          </section>
        ) : null}

        {tab === "onboarding" ? (
          <section style={opsSanityCardStyle}>
            <p style={summary24hHintStyle}>Progresso: {onboardingPct}%</p>
            <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
              {onboarding.map((m) => (
                <li
                  key={m.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 8,
                    padding: "8px 0",
                    borderTop: "1px solid #334155",
                    fontSize: 13,
                  }}
                >
                  <span>
                    {m.milestone_label} <code>({m.milestone_code})</code> — {m.status}
                  </span>
                  {canMutate ? (
                    <button type="button" style={buttonGhostStyle} onClick={() => void onMarkOnboardingDone(m.id)}>
                      DONE
                    </button>
                  ) : null}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {(tab === "ecommerce" || tab === "logistics") && (
          <section style={opsSanityCardStyle}>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                name
                <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} style={healthLocalFilterInputStyle} />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                code
                <input value={form.code} onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))} style={healthLocalFilterInputStyle} />
              </label>
            </div>
            {canMutate ? (
              <div style={toolbarStyle}>
                <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreate()} disabled={loading || !form.name || !form.code}>
                  Criar {tab === "logistics" ? "logística" : "e-commerce"}
                </button>
              </div>
            ) : null}
            <PartnerTable ecItems={ecItems} lgItems={lgItems} show={tab} />
          </section>
        )}

        {tab === "integrations" && (
          <section style={opsSanityCardStyle}>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                webhook URL
                <input value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} style={healthLocalFilterInputStyle} />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                secret
                <input value={webhookSecret} onChange={(e) => setWebhookSecret(e.target.value)} style={healthLocalFilterInputStyle} />
              </label>
            </div>
            <div style={toolbarStyle}>
              <button type="button" style={buttonGhostStyle} onClick={() => void onWebhook()} disabled={!canMutate || !selectedId || !webhookUrl}>
                Salvar webhook
              </button>
              <button type="button" style={buttonGhostStyle} onClick={() => void onRotate()} disabled={!canMutate || !selectedId}>
                Rotacionar API key
              </button>
            </div>
          </section>
        )}

        {tab === "contacts" && (
          <section style={opsSanityCardStyle}>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                nome
                <input value={contactName} onChange={(e) => setContactName(e.target.value)} style={healthLocalFilterInputStyle} />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                email
                <input value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} style={healthLocalFilterInputStyle} />
              </label>
            </div>
            {canMutate ? (
              <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreateContact()} disabled={!contactName}>
                Adicionar contato
              </button>
            ) : null}
            <JsonBlock title="Contatos" data={contacts} />
          </section>
        )}

        {tab === "settlements" && (
          <section style={opsSanityCardStyle}>
            {canMutate ? (
              <button type="button" style={buttonPrimaryStyle} onClick={() => void onGenerateSettlement()} disabled={!selectedId}>
                Gerar settlement (demo)
              </button>
            ) : null}
            <JsonBlock title="Settlements" data={settlements} />
          </section>
        )}

        {tab === "integration_health" && (
          <section style={opsSanityCardStyle}>
            <button type="button" style={buttonPrimaryStyle} onClick={() => void onProbeHealth()} disabled={!selectedId}>
              Executar probe
            </button>
            <JsonBlock title="Integration health" data={integrationHealth} />
          </section>
        )}

        {tab === "webhook_monitor" && <JsonBlock title="Webhook deliveries" data={webhookDeliveries} />}
        {tab === "outbox" && <JsonBlock title="Outbox eventos" data={outbox} />}
        {tab === "service_areas" && <JsonBlock title="Service areas" data={serviceAreas} />}
        {tab === "billing" && (
          <>
            <JsonBlock title="Planos" data={billingPlans} />
            <JsonBlock title="Ciclos" data={billingCycles} />
            <JsonBlock title="Line items" data={lineItems} />
          </>
        )}
        {tab === "invoices" && <JsonBlock title="NF B2B" data={invoices} />}
        {tab === "credits" && <JsonBlock title="Credit notes" data={creditNotes} />}
        {tab === "holds" && <JsonBlock title="Payment holds" data={paymentHolds} />}
        {tab === "commission" && <JsonBlock title="Comissões" data={commissions} />}
        {tab === "sla" && <JsonBlock title="SLA agreements" data={slaItems} />}
        {tab === "status" && <JsonBlock title="Status history" data={statusHistory} />}
        {tab === "stores" && <JsonBlock title="Lojas C&C" data={stores} />}

        {tab === "global_ops" ? (
          <section style={opsSanityCardStyle}>
            <p style={summary24hHintStyle}>
              Corredores internacionais, certificações (espelho marketplace no locker_central) e SLA por rota.
            </p>
            <div style={toolbarStyle}>
              {canMutate ? (
                <>
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    disabled={loading}
                    onClick={async () => {
                      try {
                        await apiFetch("/ecosystem/global-ops/seed", { headers, method: "POST" });
                        await apiFetch("/ecosystem/global-ops/certifications/mirror", { headers, method: "POST" });
                        const sum = await apiFetch("/ecosystem/global-ops/summary", { headers });
                        const corridors = await apiFetch("/ecosystem/global-ops/corridors", { headers });
                        const sla = await apiFetch("/ecosystem/global-ops/corridor-sla", { headers });
                        setGlobalOpsSummary(sum);
                        setGlobalCorridors(corridors);
                        setCorridorSla(sla);
                        setOk("Global OPS atualizado.");
                      } catch (e) {
                        setErr(normalizeNetworkError(e, API));
                      }
                    }}
                  >
                    Seed Global OPS + espelho certificações
                  </button>
                </>
              ) : null}
            </div>
            {globalOpsSummary ? <JsonBlock title="Resumo Global OPS" data={globalOpsSummary} /> : null}
            {globalCorridors.length > 0 ? <JsonBlock title="Corredores" data={globalCorridors} /> : null}
            {corridorSla.length > 0 ? <JsonBlock title="SLA por corredor" data={corridorSla} /> : null}
          </section>
        ) : null}

        {tab === "capability_webhooks" ? (
          <section style={opsSanityCardStyle}>
            <p style={summary24hHintStyle}>Webhooks por capability, fila dead-letter e replay em lote.</p>
            <div style={toolbarStyle}>
              {canMutate ? (
                <>
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    disabled={loading}
                    onClick={async () => {
                      try {
                        const wh = await apiFetch("/ecosystem/capability-webhooks/mirror-from-capabilities", {
                          headers,
                          method: "POST",
                        });
                        setOk(`Webhooks espelhados: ${wh.total ?? wh.mirrored_from_marketplace ?? "ok"}`);
                      } catch (e) {
                        setErr(normalizeNetworkError(e, API));
                      }
                    }}
                  >
                    Espelhar webhooks
                  </button>
                  <button
                    type="button"
                    style={buttonGhostStyle}
                    disabled={loading}
                    onClick={async () => {
                      try {
                        const dlq = await apiFetch(
                          "/ecosystem/capability-webhooks/deliveries?status=DEAD_LETTER",
                          { headers },
                        );
                        setDeadLetterDeliveries(dlq.items ?? dlq);
                        setOk(`DLQ: ${(dlq.items ?? dlq).length} entregas`);
                      } catch (e) {
                        setErr(normalizeNetworkError(e, API));
                      }
                    }}
                  >
                    Atualizar DLQ
                  </button>
                  <button
                    type="button"
                    style={buttonGhostStyle}
                    disabled={loading}
                    onClick={async () => {
                      try {
                        const r = await apiFetch(
                          "/ecosystem/capability-webhooks/deliveries/replay-dead-letter?limit=25",
                          { headers, method: "POST" },
                        );
                        setOk(`Replay: ${r.replayed}/${r.requested} (${r.succeeded} OK)`);
                      } catch (e) {
                        setErr(normalizeNetworkError(e, API));
                      }
                    }}
                  >
                    Replay dead-letter (lote)
                  </button>
                </>
              ) : null}
            </div>
            {deadLetterDeliveries.length > 0 ? (
              <JsonBlock title="Dead-letter" data={deadLetterDeliveries} />
            ) : (
              <p style={mutedTextStyle}>Nenhuma entrega em dead-letter.</p>
            )}
          </section>
        ) : null}

        {tab === "ecosystem" ? (
          <section style={opsSanityCardStyle}>
            <p style={summary24hHintStyle}>
              Catálogo global (InPost, DHL, Magalu, Mercado Livre, Amazon, DPD, Correios, CTT, Worten, El Corte Inglés…)
              — espelho de marketplace_channel_partners.
            </p>
            <div style={toolbarStyle}>
              {canMutate ? (
                <button
                  type="button"
                  style={buttonPrimaryStyle}
                  disabled={loading}
                  onClick={async () => {
                    try {
                      await apiFetch("/ecosystem/players/sync-catalog", { headers, method: "POST" });
                      setOk("Catálogo sincronizado.");
                      await loadDomain();
                    } catch (e) {
                      setErr(normalizeNetworkError(e, API));
                    }
                  }}
                >
                  Sync catálogo mundial
                </button>
              ) : null}
              <label style={{ fontSize: 12, color: "#94a3b8", display: "flex", alignItems: "center", gap: 6 }}>
                <input
                  type="checkbox"
                  checked={ecoPriorityOnly}
                  onChange={(e) => setEcoPriorityOnly(e.target.checked)}
                />
                Só prioritários
              </label>
            </div>
            <JsonBlock title={`Players (${ecosystemPlayers.length})`} data={ecosystemPlayers} />
            <JsonBlock title={`Vínculos — ${selectedId}`} data={ecosystemLinks} />
          </section>
        ) : null}

        {tab === "overview" && performance.length > 0 ? <JsonBlock title="Performance" data={performance} /> : null}
      </section>
    </div>
  );
}

function PartnerTable({ ecItems, lgItems, show }) {
  const rows =
    show === "logistics"
      ? lgItems.map((p) => ["LG", p.code, p.name, p.active ? "Y" : "N"])
      : ecItems.map((p) => ["EC", p.code, p.name, p.active ? "Y" : "N"]);
  if (!rows.length) return <p style={summary24hHintStyle}>Nenhum parceiro — Seed ou Listar.</p>;
  return (
    <div style={{ overflowX: "auto", marginTop: 12 }}>
      <table style={tableStyle}>
        <thead>
          <tr>
            {["tipo", "code", "name", "ativo"].map((h) => (
              <th key={h} style={thStyle}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row[0]}-${row[1]}`}>
              {row.map((cell, i) => (
                <td key={i} style={tdStyle}>
                  {i === 1 ? <code>{cell}</code> : cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

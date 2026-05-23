
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
  mutedTextStyle,
  okBannerStyle,
  pageStyle,
  tabButtonStyle,
  tableStyle,
  tdStyle,
  thStyle,
  toolbarStyle,
} from "../styles/opsShellStyles";

const BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const INTERNAL = String(import.meta.env.VITE_INTERNAL_TOKEN || "").trim();
const API = `${BASE}/internal/rentals`;
const PAGE_VERSION = "ops/rentals/admin v2.0";

const TABS = [
  { id: "overview", label: "Visão geral" },
  { id: "networks", label: "Redes mundiais" },
  { id: "corridors", label: "Corredores" },
  { id: "operators", label: "Operadores B2B" },
  { id: "plans", label: "Planos" },
  { id: "contracts", label: "Contratos" },
  { id: "billing", label: "Faturamento" },
  { id: "sla", label: "SLA" },
  { id: "events", label: "Eventos" },
  { id: "integrations", label: "Integrações" },
  { id: "onboarding", label: "Onboarding KYB" },
  { id: "capacity", label: "Capacidade" },
  { id: "settlements", label: "Liquidações" },
  { id: "premium", label: "SLA & disputas" },
  { id: "advanced", label: "Avançado" },
];

function parseError(payload, fallback = "Falha na API rentals.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail?.message) return String(payload.detail.message);
  if (payload?.detail?.type) return `${payload.detail.type}: ${payload.detail.message || JSON.stringify(payload.detail)}`;
  if (typeof payload?.detail === "object") return JSON.stringify(payload.detail);
  if (payload?.message) return String(payload.message);
  return fallback;
}

function formatBrl(cents) {
  const n = Number(cents);
  if (!Number.isFinite(n)) return "—";
  return `R$ ${(n / 100).toFixed(2)}`;
}

function buildHeaders() {
  return {
    Accept: "application/json",
    "Content-Type": "application/json",
    ...(INTERNAL ? { "X-Internal-Token": INTERNAL } : {}),
  };
}

export default function OpsRentalAdminPage() {
  const { hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get("tab") || "overview";
  const [tab, setTab] = useState(TABS.some((t) => t.id === initialTab) ? initialTab : "overview");
  const [plans, setPlans] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [networks, setNetworks] = useState([]);
  const [corridors, setCorridors] = useState([]);
  const [operators, setOperators] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [slaPolicies, setSlaPolicies] = useState([]);
  const [deliveries, setDeliveries] = useState([]);
  const [contractEvents, setContractEvents] = useState([]);
  const [eventsContractId, setEventsContractId] = useState("");
  const [webhooks, setWebhooks] = useState([]);
  const [apiKeys, setApiKeys] = useState([]);
  const [ecosystemCatalog, setEcosystemCatalog] = useState(null);
  const [premiumSummary, setPremiumSummary] = useState(null);
  const [onboarding, setOnboarding] = useState([]);
  const [capacity, setCapacity] = useState([]);
  const [settlements, setSettlements] = useState([]);
  const [slaBreaches, setSlaBreaches] = useState([]);
  const [disputes, setDisputes] = useState([]);
  const [renewalOffers, setRenewalOffers] = useState([]);
  const [networkHealth, setNetworkHealth] = useState([]);
  const [accessPasses, setAccessPasses] = useState([]);
  const [deposits, setDeposits] = useState([]);
  const [slotBlocks, setSlotBlocks] = useState([]);
  const [pricingRules, setPricingRules] = useState([]);
  const [dunningCases, setDunningCases] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [priceQuote, setPriceQuote] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const [lastApiKey, setLastApiKey] = useState("");
  const [planForm, setPlanForm] = useState({
    name: "",
    locker_id: "",
    slot_size: "M",
    billing_cycle: "MONTHLY",
    amount_cents: 9900,
  });
  const [contractForm, setContractForm] = useState({
    locker_id: "",
    slot_label: "01A",
    plan_id: "",
    renter_name: "",
    status: "PENDING",
  });
  const [webhookForm, setWebhookForm] = useState({
    tenant_id: "tenant-inpost-br",
    url: "https://hooks.example.com/rentals",
    secret: "",
  });
  const [rotateTenant, setRotateTenant] = useState("tenant-inpost-br");
  const headers = useMemo(() => buildHeaders(), []);

  const setTabAndUrl = (id) => {
    setTab(id);
    const next = new URLSearchParams(searchParams);
    if (id === "overview") next.delete("tab");
    else next.set("tab", id);
    setSearchParams(next, { replace: true });
  };

  useEffect(() => {
    const fromUrl = searchParams.get("tab") || "overview";
    setTab(TABS.some((t) => t.id === fromUrl) ? fromUrl : "overview");
  }, [searchParams]);

  const load = useCallback(async () => {
    if (!INTERNAL || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const [s, p, c, n, cor, op, inv, sla, del, w, k, eco, ps, ob, cap, stl, br, disp, ren, nh, ap, dep, sb, pr, dun, tr] = await Promise.all([
        fetch(`${API}/analytics/summary`, { headers }),
        fetch(`${API}/plans?active_only=false`, { headers }),
        fetch(`${API}/contracts?limit=100`, { headers }),
        fetch(`${API}/networks?active_only=false`, { headers }),
        fetch(`${API}/corridors`, { headers }),
        fetch(`${API}/operators`, { headers }),
        fetch(`${API}/billing/invoices?limit=100`, { headers }),
        fetch(`${API}/sla-policies`, { headers }),
        fetch(`${API}/webhook-deliveries?limit=50`, { headers }),
        fetch(`${API}/webhooks`, { headers }),
        fetch(`${API}/api-keys`, { headers }),
        fetch(`${API}/ecosystem/catalog`, { headers }),
        fetch(`${API}/analytics/premium-summary`, { headers }),
        fetch(`${API}/onboarding`, { headers }),
        fetch(`${API}/capacity?days=14`, { headers }),
        fetch(`${API}/settlements`, { headers }),
        fetch(`${API}/sla-breaches`, { headers }),
        fetch(`${API}/disputes`, { headers }),
        fetch(`${API}/renewal-offers`, { headers }),
        fetch(`${API}/analytics/network-health`, { headers }),
        fetch(`${API}/access-passes`, { headers }),
        fetch(`${API}/deposits`, { headers }),
        fetch(`${API}/slot-blocks`, { headers }),
        fetch(`${API}/pricing-rules`, { headers }),
        fetch(`${API}/dunning`, { headers }),
        fetch(`${API}/transfers`, { headers }),
      ]);
      const sj = await s.json().catch(() => ({}));
      const pj = await p.json().catch(() => ({}));
      const cj = await c.json().catch(() => ({}));
      const nj = await n.json().catch(() => ({}));
      const corj = await cor.json().catch(() => ({}));
      const opj = await op.json().catch(() => ({}));
      const invj = await inv.json().catch(() => ({}));
      const slaj = await sla.json().catch(() => ({}));
      const delj = await del.json().catch(() => ({}));
      const wj = await w.json().catch(() => ({}));
      const kj = await k.json().catch(() => ({}));
      const ecoj = await eco.json().catch(() => ({}));
      const psj = await ps.json().catch(() => ({}));
      const obj = await ob.json().catch(() => ({}));
      const capj = await cap.json().catch(() => ({}));
      const stlj = await stl.json().catch(() => ({}));
      const brj = await br.json().catch(() => ({}));
      const dispj = await disp.json().catch(() => ({}));
      const renj = await ren.json().catch(() => ({}));
      const nhj = await nh.json().catch(() => ({}));
      const apj = await ap.json().catch(() => ({}));
      const depj = await dep.json().catch(() => ({}));
      const sbj = await sb.json().catch(() => ({}));
      const prj = await pr.json().catch(() => ({}));
      const dunj = await dun.json().catch(() => ({}));
      const trj = await tr.json().catch(() => ({}));
      const failures = [];
      if (!p.ok) failures.push(`planos: ${parseError(pj)}`);
      if (!c.ok) failures.push(`contratos: ${parseError(cj)}`);
      if (!s.ok) failures.push(`analytics: ${parseError(sj)}`);
      if (failures.length) throw new Error(failures.join(" | "));
      setSummary(sj.summary || null);
      setPlans(pj.items || []);
      setContracts(cj.items || []);
      setNetworks(nj.items || []);
      setCorridors(corj.items || []);
      setOperators(opj.items || []);
      setInvoices(invj.items || []);
      setSlaPolicies(slaj.items || []);
      setDeliveries(delj.items || []);
      setWebhooks(wj.items || []);
      setApiKeys(kj.items || []);
      if (eco.ok && ecoj.catalog) setEcosystemCatalog(ecoj.catalog);
      if (ps.ok) setPremiumSummary(psj.summary || null);
      if (ob.ok) setOnboarding(obj.items || []);
      if (cap.ok) setCapacity(capj.items || []);
      if (stl.ok) setSettlements(stlj.items || []);
      if (br.ok) setSlaBreaches(brj.items || []);
      if (disp.ok) setDisputes(dispj.items || []);
      if (ren.ok) setRenewalOffers(renj.items || []);
      if (nh.ok) setNetworkHealth(nhj.items || []);
      if (ap.ok) setAccessPasses(apj.items || []);
      if (dep.ok) setDeposits(depj.items || []);
      if (sb.ok) setSlotBlocks(sbj.items || []);
      if (pr.ok) setPricingRules(prj.items || []);
      if (dun.ok) setDunningCases(dunj.items || []);
      if (tr.ok) setTransfers(trj.items || []);
      if (!eventsContractId && (cj.items || []).length) {
        setEventsContractId(cj.items[0].id);
      }
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }, [headers, canMutate, eventsContractId]);

  const loadContractEvents = useCallback(async () => {
    if (!INTERNAL || !eventsContractId) return;
    try {
      const r = await fetch(`${API}/contracts/${encodeURIComponent(eventsContractId)}/events`, { headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setContractEvents(j.items || []);
    } catch (e) {
      setErr(String(e.message || e));
    }
  }, [headers, eventsContractId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (tab === "events") void loadContractEvents();
  }, [tab, loadContractEvents]);

  const onSeed = async () => {
    if (!INTERNAL || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seed`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j, `Seed falhou (HTTP ${r.status})`));
      const mig = j.migrations_applied?.length ? ` · migrações: ${j.migrations_applied.join(", ")}` : "";
      setOk(`Seed OK: ${JSON.stringify(j.seeded || j)}${mig}`);
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const onCreatePlan = async () => {
    if (!planForm.name) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/plans`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          ...planForm,
          locker_id: planForm.locker_id || null,
          amount_cents: Number(planForm.amount_cents),
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Plano ${j.name} criado.`);
      setPlanForm({ name: "", locker_id: "", slot_size: "M", billing_cycle: "MONTHLY", amount_cents: 9900 });
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const onCreateContract = async () => {
    if (!contractForm.locker_id || !contractForm.slot_label) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/contracts`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          ...contractForm,
          plan_id: contractForm.plan_id || null,
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Contrato ${j.contract?.id} criado.`);
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const onWebhook = async () => {
    if (!webhookForm.tenant_id || !webhookForm.url) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/webhooks/${encodeURIComponent(webhookForm.tenant_id)}`, {
        method: "PUT",
        headers,
        body: JSON.stringify({
          tenant_id: webhookForm.tenant_id,
          url: webhookForm.url,
          secret: webhookForm.secret || undefined,
          events: ["rental.contract.created", "rental.contract.activated", "rental.billing.due"],
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Webhook salvo. Secret: ${j.webhook_secret || "(gerado)"}`);
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const onRotate = async () => {
    if (!rotateTenant) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/api-keys/${encodeURIComponent(rotateTenant)}/rotate`, {
        method: "POST",
        headers,
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setLastApiKey(j.api_key || "");
      setOk(`API key rotacionada (${j.key_prefix}…). Copie agora.`);
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  if (!canMutate) {
    return (
      <div style={pageStyle}>
        <section style={cardStyle}>
          <OpsPageTitleHeader title="OPS — Rental (aluguel de slots)" />
          <p style={criticalBannerStyle}>Requer perfil admin_operacao.</p>
        </section>
      </div>
    );
  }

  const activeContracts = summary?.active_contracts ?? contracts.filter((c) => c.status === "ACTIVE").length;
  const mrrCents = summary?.mrr_cents ?? 0;

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Rental (planos, contratos, integrações)" />
        <p style={mutedTextStyle}>
          Catálogo mundial: lockers, carriers (UPS, FedEx, GLS), marketplaces (Shopee, Walmart), agregadores
          (Melhor Envio, Intelipost) e food delivery (iFood, Uber Eats) · API <code>{API}</code> · {PAGE_VERSION}
        </p>
        {ecosystemCatalog ? (
          <p style={mutedTextStyle}>
            Referência: {ecosystemCatalog.networks_total} redes · prioridade OPS:{" "}
            {(ecosystemCatalog.priority_codes || []).join(", ")} · seed complementa metadados por{" "}
            <code>code</code>
          </p>
        ) : null}
        <p style={mutedTextStyle}>
          Atalhos:{" "}
          <Link to="/ops/rentals/contracts" style={{ color: "#93C5FD" }}>
            contratos (lista)
          </Link>{" "}
          ·{" "}
          <Link to="/ops/rentals/plans" style={{ color: "#93C5FD" }}>
            planos (lista)
          </Link>
        </p>
        {!INTERNAL ? <p style={criticalBannerStyle}>Configure VITE_INTERNAL_TOKEN.</p> : null}
        {err ? <p style={criticalBannerStyle}>{err}</p> : null}
        {ok ? <p style={okBannerStyle}>{ok}</p> : null}
        {lastApiKey ? <p style={apiKeyBannerStyle}>API key: {lastApiKey}</p> : null}

        <div style={{ ...toolbarStyle, marginTop: 12 }}>
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              style={tabButtonStyle(tab === t.id)}
              onClick={() => setTabAndUrl(t.id)}
            >
              {t.label}
            </button>
          ))}
          <button type="button" style={buttonGhostStyle} onClick={() => void load()} disabled={loading || !INTERNAL}>
            Atualizar
          </button>
          <button type="button" style={buttonPrimaryStyle} onClick={() => void onSeed()} disabled={loading || !INTERNAL}>
            Seed demo
          </button>
        </div>

        {tab === "overview" ? (
          <div style={{ marginTop: 16, display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))" }}>
            {[
              ["Redes ativas", summary?.active_networks ?? networks.length],
              ["Operadores", summary?.active_operators ?? operators.length],
              ["Planos", summary?.active_plans ?? plans.length],
              ["Contratos ativos", activeContracts],
              ["MRR", formatBrl(mrrCents)],
              ["Faturas em atraso", summary?.overdue_invoices ?? 0],
              ["Receita paga", formatBrl(summary?.paid_invoice_cents ?? 0)],
              ["Webhooks", webhooks.length],
              ["Onboarding LIVE", premiumSummary?.onboarding_live ?? "—"],
              ["SLA breaches abertos", premiumSummary?.open_sla_breaches ?? "—"],
              ["Utilização média %", premiumSummary?.avg_utilization_pct ?? "—"],
              ["Disputas abertas", premiumSummary?.open_disputes ?? "—"],
            ].map(([label, val]) => (
              <div key={label} style={cardStyle}>
                <strong>{label}</strong>
                <p style={mutedTextStyle}>{val}</p>
              </div>
            ))}
          </div>
        ) : null}

        {tab === "networks" ? (
          <div style={{ marginTop: 16 }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["code", "name", "network_type", "hardware_vendor", "países", "active"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {networks.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.code}</td>
                    <td style={tdStyle}>{row.name}</td>
                    <td style={tdStyle}>{row.network_type}</td>
                    <td style={tdStyle}>{row.hardware_vendor ?? "—"}</td>
                    <td style={tdStyle}>{(row.primary_countries || []).join(", ")}</td>
                    <td style={tdStyle}>{String(row.active)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "corridors" ? (
          <div style={{ marginTop: 16 }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["network", "origem", "destino", "sla_h", "moeda"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {corridors.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.network_code ?? row.network_id}</td>
                    <td style={tdStyle}>{row.origin_country}</td>
                    <td style={tdStyle}>{row.destination_country}</td>
                    <td style={tdStyle}>{row.sla_hours}</td>
                    <td style={tdStyle}>{row.currency}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "operators" ? (
          <div style={{ marginTop: 16 }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["operator_code", "legal_name", "network", "tenant_id", "comissão bps", "status"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {operators.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.operator_code}</td>
                    <td style={tdStyle}>{row.legal_name}</td>
                    <td style={tdStyle}>{row.network_code ?? "—"}</td>
                    <td style={tdStyle}>{row.tenant_id ?? "—"}</td>
                    <td style={tdStyle}>{row.commission_bps}</td>
                    <td style={tdStyle}>{row.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "billing" ? (
          <div style={{ marginTop: 16 }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["invoice_number", "contract_id", "valor", "status", "due_at"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {invoices.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.invoice_number}</td>
                    <td style={tdStyle}>{row.contract_id}</td>
                    <td style={tdStyle}>{formatBrl(row.amount_cents)}</td>
                    <td style={tdStyle}>{row.status}</td>
                    <td style={tdStyle}>{row.due_at ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "sla" ? (
          <div style={{ marginTop: 16 }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["network", "metric_code", "target", "unit", "penalty bps"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {slaPolicies.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.network_code}</td>
                    <td style={tdStyle}>{row.metric_code}</td>
                    <td style={tdStyle}>{row.target_value}</td>
                    <td style={tdStyle}>{row.unit}</td>
                    <td style={tdStyle}>{row.breach_penalty_bps}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "events" ? (
          <div style={{ marginTop: 16 }}>
            <div style={toolbarStyle}>
              <label style={{ fontSize: 12, color: "#CBD5E1" }}>
                contract_id
                <input
                  value={eventsContractId}
                  onChange={(e) => setEventsContractId(e.target.value)}
                  style={{ display: "block", marginTop: 4, padding: 8, borderRadius: 8, minWidth: 280 }}
                />
              </label>
              <button type="button" style={buttonPrimaryStyle} onClick={() => void loadContractEvents()}>
                Carregar eventos
              </button>
            </div>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["event_type", "actor", "created_at", "payload"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {contractEvents.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.event_type}</td>
                    <td style={tdStyle}>{row.actor}</td>
                    <td style={tdStyle}>{row.created_at}</td>
                    <td style={tdStyle}>
                      <code style={{ fontSize: 10 }}>{JSON.stringify(row.payload || {})}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "plans" ? (
          <div style={{ marginTop: 16 }}>
            <div style={toolbarStyle}>
              <input
                placeholder="Nome do plano"
                value={planForm.name}
                onChange={(e) => setPlanForm((f) => ({ ...f, name: e.target.value }))}
                style={{ padding: 8, borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" }}
              />
              <input
                placeholder="locker_id (opcional)"
                value={planForm.locker_id}
                onChange={(e) => setPlanForm((f) => ({ ...f, locker_id: e.target.value }))}
                style={{ padding: 8, borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" }}
              />
              <select
                value={planForm.billing_cycle}
                onChange={(e) => setPlanForm((f) => ({ ...f, billing_cycle: e.target.value }))}
                style={{ padding: 8, borderRadius: 8 }}
              >
                {["DAILY", "WEEKLY", "MONTHLY", "QUARTERLY", "YEARLY"].map((b) => (
                  <option key={b} value={b}>
                    {b}
                  </option>
                ))}
              </select>
              <input
                type="number"
                value={planForm.amount_cents}
                onChange={(e) => setPlanForm((f) => ({ ...f, amount_cents: e.target.value }))}
                style={{ width: 120, padding: 8, borderRadius: 8 }}
              />
              <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreatePlan()} disabled={loading}>
                Criar plano
              </button>
            </div>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["name", "locker_id", "slot_size", "billing_cycle", "valor", "active"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {plans.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.name}</td>
                    <td style={tdStyle}>{row.locker_id ?? "—"}</td>
                    <td style={tdStyle}>{row.slot_size ?? "—"}</td>
                    <td style={tdStyle}>{row.billing_cycle}</td>
                    <td style={tdStyle}>{formatBrl(row.amount_cents)}</td>
                    <td style={tdStyle}>{String(row.active)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "contracts" ? (
          <div style={{ marginTop: 16 }}>
            <div style={toolbarStyle}>
              <input
                placeholder="locker_id"
                value={contractForm.locker_id}
                onChange={(e) => setContractForm((f) => ({ ...f, locker_id: e.target.value }))}
                style={{ padding: 8, borderRadius: 8, minWidth: 160 }}
              />
              <input
                placeholder="slot_label"
                value={contractForm.slot_label}
                onChange={(e) => setContractForm((f) => ({ ...f, slot_label: e.target.value }))}
                style={{ padding: 8, borderRadius: 8, width: 90 }}
              />
              <input
                placeholder="plan_id"
                value={contractForm.plan_id}
                onChange={(e) => setContractForm((f) => ({ ...f, plan_id: e.target.value }))}
                style={{ padding: 8, borderRadius: 8, minWidth: 200 }}
              />
              <input
                placeholder="renter_name"
                value={contractForm.renter_name}
                onChange={(e) => setContractForm((f) => ({ ...f, renter_name: e.target.value }))}
                style={{ padding: 8, borderRadius: 8 }}
              />
              <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreateContract()} disabled={loading}>
                Criar contrato
              </button>
            </div>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["id", "locker_id", "renter_name", "status", "billing", "valor", "detalhe"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {contracts.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.id}</td>
                    <td style={tdStyle}>{row.locker_id}</td>
                    <td style={tdStyle}>{row.renter_name ?? "—"}</td>
                    <td style={tdStyle}>{row.status}</td>
                    <td style={tdStyle}>{row.billing_cycle}</td>
                    <td style={tdStyle}>{formatBrl(row.amount_cents)}</td>
                    <td style={tdStyle}>
                      <Link to={`/ops/rentals/contracts/${encodeURIComponent(row.id)}`} style={{ color: "#93C5FD" }}>
                        abrir
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "integrations" ? (
          <div style={{ marginTop: 16, display: "grid", gap: 16 }}>
            <div>
              <h3 style={{ color: "#E2E8F0" }}>Entregas webhook (dead-letter / retry)</h3>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["tenant_id", "event_type", "status", "attempt", "response"].map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {deliveries.map((d) => (
                    <tr key={d.id}>
                      <td style={tdStyle}>{d.tenant_id}</td>
                      <td style={tdStyle}>{d.event_type}</td>
                      <td style={tdStyle}>{d.status}</td>
                      <td style={tdStyle}>{d.attempt}</td>
                      <td style={tdStyle}>{d.response_code ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h3 style={{ color: "#E2E8F0" }}>Webhook por tenant</h3>
              <div style={toolbarStyle}>
                <input
                  value={webhookForm.tenant_id}
                  onChange={(e) => setWebhookForm((f) => ({ ...f, tenant_id: e.target.value }))}
                  placeholder="tenant_id"
                  style={{ padding: 8, borderRadius: 8, minWidth: 160 }}
                />
                <input
                  value={webhookForm.url}
                  onChange={(e) => setWebhookForm((f) => ({ ...f, url: e.target.value }))}
                  placeholder="https://..."
                  style={{ padding: 8, borderRadius: 8, flex: 1, minWidth: 240 }}
                />
                <button type="button" style={buttonPrimaryStyle} onClick={() => void onWebhook()} disabled={loading}>
                  Salvar webhook
                </button>
              </div>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["tenant_id", "url", "active", "events"].map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {webhooks.map((w) => (
                    <tr key={w.id}>
                      <td style={tdStyle}>{w.tenant_id}</td>
                      <td style={tdStyle}>{w.url}</td>
                      <td style={tdStyle}>{String(w.active)}</td>
                      <td style={tdStyle}>{(w.events || []).join(", ")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h3 style={{ color: "#E2E8F0" }}>Rotação API key</h3>
              <div style={toolbarStyle}>
                <input
                  value={rotateTenant}
                  onChange={(e) => setRotateTenant(e.target.value)}
                  placeholder="tenant_id"
                  style={{ padding: 8, borderRadius: 8 }}
                />
                <button type="button" style={buttonPrimaryStyle} onClick={() => void onRotate()} disabled={loading}>
                  Rotacionar chave
                </button>
              </div>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["tenant_id", "key_prefix", "label", "revoked_at"].map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {apiKeys.map((k) => (
                    <tr key={k.id}>
                      <td style={tdStyle}>{k.tenant_id}</td>
                      <td style={tdStyle}>{k.key_prefix}…</td>
                      <td style={tdStyle}>{k.label ?? "—"}</td>
                      <td style={tdStyle}>{k.revoked_at ?? "ativa"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        {tab === "onboarding" ? (
          <div style={{ marginTop: 16 }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["rede", "status", "tier", "compliance", "reviewer"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {onboarding.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.network_code}</td>
                    <td style={tdStyle}>{row.status}</td>
                    <td style={tdStyle}>{row.kyb_tier}</td>
                    <td style={tdStyle}>{row.compliance_score ?? "—"}</td>
                    <td style={tdStyle}>{row.reviewer ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "capacity" ? (
          <div style={{ marginTop: 16 }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["rede", "data", "ocupação %", "slots", "health score"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {capacity.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.network_code}</td>
                    <td style={tdStyle}>{row.snapshot_date}</td>
                    <td style={tdStyle}>{row.utilization_pct}</td>
                    <td style={tdStyle}>
                      {row.occupied_slots}/{row.total_slots}
                    </td>
                    <td style={tdStyle}>
                      {networkHealth.find((h) => h.code === row.network_code)?.health_score ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "settlements" ? (
          <div style={{ marginTop: 16 }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  {["batch", "operador", "bruto", "líquido", "status"].map((h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {settlements.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.batch_code}</td>
                    <td style={tdStyle}>{row.operator_name ?? row.operator_code}</td>
                    <td style={tdStyle}>{formatBrl(row.gross_cents)}</td>
                    <td style={tdStyle}>{formatBrl(row.net_cents)}</td>
                    <td style={tdStyle}>{row.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "premium" ? (
          <div style={{ marginTop: 16, display: "grid", gap: 20 }}>
            <div>
              <h3 style={{ color: "#E2E8F0" }}>Incidentes SLA</h3>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["rede", "métrica", "medido", "meta", "status", "penalidade"].map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {slaBreaches.map((row) => (
                    <tr key={row.id}>
                      <td style={tdStyle}>{row.network_code}</td>
                      <td style={tdStyle}>{row.metric_code}</td>
                      <td style={tdStyle}>{row.measured_value}</td>
                      <td style={tdStyle}>{row.target_value}</td>
                      <td style={tdStyle}>{row.status}</td>
                      <td style={tdStyle}>{formatBrl(row.penalty_cents)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h3 style={{ color: "#E2E8F0" }}>Disputas</h3>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["contrato", "tipo", "valor", "status", "motivo"].map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {disputes.map((row) => (
                    <tr key={row.id}>
                      <td style={tdStyle}>{row.contract_id?.slice(0, 8)}…</td>
                      <td style={tdStyle}>{row.dispute_type}</td>
                      <td style={tdStyle}>{formatBrl(row.amount_cents)}</td>
                      <td style={tdStyle}>{row.status}</td>
                      <td style={tdStyle}>{row.reason ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h3 style={{ color: "#E2E8F0" }}>Ofertas de renovação</h3>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["locatário", "valor", "válido até", "status"].map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {renewalOffers.map((row) => (
                    <tr key={row.id}>
                      <td style={tdStyle}>{row.renter_name ?? row.contract_id?.slice(0, 8)}</td>
                      <td style={tdStyle}>{formatBrl(row.offer_amount_cents)}</td>
                      <td style={tdStyle}>{row.valid_until}</td>
                      <td style={tdStyle}>{row.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        {tab === "advanced" ? (
          <div style={{ marginTop: 16, display: "grid", gap: 20 }}>
            <div style={toolbarStyle}>
              <button
                type="button"
                style={buttonGhostStyle}
                onClick={async () => {
                  const r = await fetch(`${API}/pricing/quote`, {
                    method: "POST",
                    headers: { ...headers, "Content-Type": "application/json" },
                    body: JSON.stringify({ slot_size: "M", billing_cycle: "MONTHLY" }),
                  });
                  const j = await r.json();
                  if (r.ok) setPriceQuote(j);
                }}
              >
                Cotação dinâmica (M/mensal)
              </button>
              <button
                type="button"
                style={buttonGhostStyle}
                onClick={async () => {
                  await fetch(`${API}/dunning/scan`, { method: "POST", headers });
                  void load();
                }}
              >
                Scan dunning
              </button>
              {priceQuote?.quoted ? (
                <span style={mutedTextStyle}>
                  Cotação: R$ {(priceQuote.amount_cents / 100).toFixed(2)} ({priceQuote.rule_code})
                </span>
              ) : null}
            </div>
            <div>
              <h3 style={{ color: "#E2E8F0" }}>Passes de acesso (PIN/QR)</h3>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["contrato", "tipo", "hint", "válido até", "usos", "status"].map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {accessPasses.map((row) => (
                    <tr key={row.id}>
                      <td style={tdStyle}>{String(row.contract_id).slice(0, 8)}…</td>
                      <td style={tdStyle}>{row.pass_type}</td>
                      <td style={tdStyle}>{row.pass_hint}</td>
                      <td style={tdStyle}>{row.valid_until}</td>
                      <td style={tdStyle}>
                        {row.use_count}/{row.max_uses}
                      </td>
                      <td style={tdStyle}>{row.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h3 style={{ color: "#E2E8F0" }}>Cauções</h3>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["contrato", "valor", "status", "motivo"].map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {deposits.map((row) => (
                    <tr key={row.id}>
                      <td style={tdStyle}>{row.renter_name ?? row.contract_id?.slice(0, 8)}</td>
                      <td style={tdStyle}>{formatBrl(row.amount_cents)}</td>
                      <td style={tdStyle}>{row.status}</td>
                      <td style={tdStyle}>{row.hold_reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h3 style={{ color: "#E2E8F0" }}>Bloqueios de slot</h3>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["locker", "slot", "tipo", "início", "fim"].map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {slotBlocks.map((row) => (
                    <tr key={row.id}>
                      <td style={tdStyle}>{row.locker_id}</td>
                      <td style={tdStyle}>{row.slot_label}</td>
                      <td style={tdStyle}>{row.block_type}</td>
                      <td style={tdStyle}>{row.starts_at}</td>
                      <td style={tdStyle}>{row.ends_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h3 style={{ color: "#E2E8F0" }}>Regras de preço</h3>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["code", "nome", "base", "surge", "rede"].map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {pricingRules.map((row) => (
                    <tr key={row.id}>
                      <td style={tdStyle}>{row.code}</td>
                      <td style={tdStyle}>{row.name}</td>
                      <td style={tdStyle}>{formatBrl(row.base_amount_cents)}</td>
                      <td style={tdStyle}>{row.surge_multiplier}</td>
                      <td style={tdStyle}>{row.network_code ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h3 style={{ color: "#E2E8F0" }}>Dunning / transferências</h3>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["tipo", "contrato", "status", "detalhe"].map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dunningCases.map((row) => (
                    <tr key={row.id}>
                      <td style={tdStyle}>dunning</td>
                      <td style={tdStyle}>{row.renter_name ?? row.contract_id?.slice(0, 8)}</td>
                      <td style={tdStyle}>{row.status}</td>
                      <td style={tdStyle}>
                        {row.stage} · {formatBrl(row.amount_due_cents)}
                      </td>
                    </tr>
                  ))}
                  {transfers.map((row) => (
                    <tr key={row.id}>
                      <td style={tdStyle}>transfer</td>
                      <td style={tdStyle}>{row.renter_name ?? row.contract_id?.slice(0, 8)}</td>
                      <td style={tdStyle}>{row.status}</td>
                      <td style={tdStyle}>
                        {row.from_slot_label} → {row.to_slot_label}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}
      </section>
    </div>
  );
}


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
  summary24hHintStyle,
  tabButtonStyle,
  tableStyle,
  tdStyle,
  thStyle,
  toolbarStyle,
} from "../styles/opsShellStyles";

const BASE = import.meta.env.VITE_MONEY_CAMBIO_ADMIN_BASE_URL || "/api/mca";
const API = `${BASE}/v1/money-cambio-admin`;
const PAGE_VERSION = "ops/money-cambio/admin v0.5-advanced-ops";

const TAB_DEFS = [
  ["overview", "Visao global"],
  ["countries", "Paises OPS"],
  ["currencies", "Moedas ISO"],
  ["methods", "Metodos"],
  ["matrix", "Metodo x Pais"],
  ["aliases", "Aliases UI"],
  ["interfaces", "Interfaces"],
  ["wallets", "Wallets"],
  ["corridors", "Corredores FX"],
  ["fx", "Taxas FX"],
  ["compliance", "Compliance"],
  ["audit", "Auditoria FX"],
  ["players", "Players ecossistema"],
  ["segments", "Segmentos"],
  ["relations", "Relacoes"],
  ["intelligence", "Intelligence"],
  ["settlements", "Settlement"],
  ["pricing", "Simulador"],
  ["rails", "Payment rails"],
  ["treasury", "Tesouraria"],
  ["fxlocks", "Travas FX"],
  ["partners", "Integracao"],
];

function parseError(payload, fallback = "Falha na API money-cambio-admin.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  return fallback;
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao (${endpoint}). Proxy ${BASE} → porta 8125. Se uvicorn ja estiver UP, nao inicie outro (./dev.sh status).`;
  }
  return raw;
}

function OverviewKpiGrid({ items }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
        gap: 12,
        marginTop: 12,
      }}
    >
      {items.map(([label, value]) => (
        <div
          key={label}
          style={{
            padding: "14px 16px",
            borderRadius: 10,
            border: "1px solid #334155",
            background: "linear-gradient(180deg, #0f172a 0%, #0b1220 100%)",
          }}
        >
          <div style={{ fontSize: 12, color: "#94a3b8", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.04em" }}>
            {label}
          </div>
          <div style={{ fontSize: 22, fontWeight: 700, color: "#f1f5f9", lineHeight: 1.2 }}>{value}</div>
        </div>
      ))}
    </div>
  );
}

export default function OpsMoneyCambioAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao") || hasRole("admin.financeiro");
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get("tab") || "overview";
  const setTab = (k) => setSearchParams({ tab: k }, { replace: true });

  const [dashboard, setDashboard] = useState(null);
  const [operatingCountries, setOperatingCountries] = useState([]);
  const [methodMatrix, setMethodMatrix] = useState([]);
  const [aliases, setAliases] = useState([]);
  const [corridors, setCorridors] = useState([]);
  const [compliance, setCompliance] = useState([]);
  const [fxAudit, setFxAudit] = useState([]);
  const [lockerPlayers, setLockerPlayers] = useState([]);
  const [ecosystemSegments, setEcosystemSegments] = useState([]);
  const [playerRelations, setPlayerRelations] = useState([]);
  const [playerSegmentFilter, setPlayerSegmentFilter] = useState("");
  const [intelDashboard, setIntelDashboard] = useState(null);
  const [readiness, setReadiness] = useState([]);
  const [insights, setInsights] = useState([]);
  const [fxAlertRules, setFxAlertRules] = useState([]);
  const [fxAlertEvents, setFxAlertEvents] = useState([]);
  const [settlementSchedules, setSettlementSchedules] = useState([]);
  const [paymentRails, setPaymentRails] = useState([]);
  const [treasury, setTreasury] = useState(null);
  const [fxLocks, setFxLocks] = useState([]);
  const [pricingForm, setPricingForm] = useState({
    amount_cents: "100000",
    player_code: "MAGALU",
    country_code: "BR",
    payment_method_code: "PIX",
  });
  const [pricingResult, setPricingResult] = useState(null);
  const [currencies, setCurrencies] = useState([]);
  const [methods, setMethods] = useState([]);
  const [interfaces, setInterfaces] = useState([]);
  const [wallets, setWallets] = useState([]);
  const [fxRates, setFxRates] = useState([]);
  const [partners, setPartners] = useState([]);
  const [currencyForm, setCurrencyForm] = useState({ code: "", name: "", symbol: "" });
  const [methodForm, setMethodForm] = useState({ code: "", name: "" });
  const [fxForm, setFxForm] = useState({ base_currency: "USD", quote_currency: "BRL", rate: "5.05" });
  const [partnerForm, setPartnerForm] = useState({ name: "", code: "", partner_type: "FX_FEED" });
  const [selectedId, setSelectedId] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [lastApiKey, setLastApiKey] = useState("");
  const [convertResult, setConvertResult] = useState(null);
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
      const [dash, oc, c, m, mx, al, i, w, cr, f, comp, aud, lp, seg, rel, intel, rd, ins, far, fae, stl, rails, treas, locks, p] =
        await Promise.all([
        fetch(`${API}/global-ops/dashboard`, { headers }),
        fetch(`${API}/operating-countries`, { headers }),
        fetch(`${API}/currencies`, { headers }),
        fetch(`${API}/payment-method-catalog`, { headers }),
        fetch(`${API}/method-country-matrix`, { headers }),
        fetch(`${API}/payment-method-ui-alias`, { headers }),
        fetch(`${API}/payment-interface-catalog`, { headers }),
        fetch(`${API}/wallet-provider-catalog`, { headers }),
        fetch(`${API}/payment-corridors`, { headers }),
        fetch(`${API}/fx-rates`, { headers }),
        fetch(`${API}/compliance-limits`, { headers }),
        fetch(`${API}/fx-rate-audit`, { headers }),
        fetch(`${API}/locker-players`, { headers }),
        fetch(`${API}/ecosystem-segments`, { headers }),
        fetch(`${API}/player-relations`, { headers }),
        fetch(`${API}/money-intelligence/dashboard`, { headers }),
        fetch(`${API}/money-intelligence/readiness`, { headers }),
        fetch(`${API}/money-intelligence/insights`, { headers }),
        fetch(`${API}/money-intelligence/fx-alert-rules`, { headers }),
        fetch(`${API}/money-intelligence/fx-alert-events`, { headers }),
        fetch(`${API}/money-intelligence/settlement-schedules`, { headers }),
        fetch(`${API}/payment-rails`, { headers }),
        fetch(`${API}/treasury/dashboard`, { headers }),
        fetch(`${API}/fx-locks`, { headers }),
        fetch(`${API}/integration-partners`, { headers }),
      ]);
      const dashJ = await dash.json().catch(() => ({}));
      const ocJ = await oc.json().catch(() => ({}));
      const cj = await c.json().catch(() => ({}));
      const mj = await m.json().catch(() => ({}));
      const mxJ = await mx.json().catch(() => ({}));
      const alJ = await al.json().catch(() => ({}));
      const ij = await i.json().catch(() => ({}));
      const wj = await w.json().catch(() => ({}));
      const crJ = await cr.json().catch(() => ({}));
      const fj = await f.json().catch(() => ({}));
      const compJ = await comp.json().catch(() => ({}));
      const audJ = await aud.json().catch(() => ({}));
      const lpJ = await lp.json().catch(() => ({}));
      const segJ = await seg.json().catch(() => ({}));
      const relJ = await rel.json().catch(() => ({}));
      const intelJ = await intel.json().catch(() => ({}));
      const rdJ = await rd.json().catch(() => ({}));
      const insJ = await ins.json().catch(() => ({}));
      const farJ = await far.json().catch(() => ({}));
      const faeJ = await fae.json().catch(() => ({}));
      const stlJ = await stl.json().catch(() => ({}));
      const railsJ = await rails.json().catch(() => ({}));
      const treasJ = await treas.json().catch(() => ({}));
      const locksJ = await locks.json().catch(() => ({}));
      const pj = await p.json().catch(() => ({}));
      if (!dash.ok) throw new Error(parseError(dashJ));
      setDashboard(dashJ);
      setOperatingCountries(ocJ.items || []);
      setCurrencies(cj.items || []);
      setMethods(mj.items || []);
      setMethodMatrix(mxJ.items || []);
      setAliases(alJ.items || []);
      setInterfaces(ij.items || []);
      setWallets(wj.items || []);
      setCorridors(crJ.items || []);
      setFxRates(fj.items || []);
      setCompliance(compJ.items || []);
      setFxAudit(audJ.items || []);
      setLockerPlayers(lpJ.items || []);
      setEcosystemSegments(segJ.items || []);
      setPlayerRelations(relJ.items || []);
      setIntelDashboard(intelJ.players_total != null ? intelJ : null);
      setReadiness(rdJ.items || []);
      setInsights(insJ.items || []);
      setFxAlertRules(farJ.items || []);
      setFxAlertEvents(faeJ.items || []);
      setSettlementSchedules(stlJ.items || []);
      setPaymentRails(railsJ.items || []);
      setTreasury(treasJ.players_active != null ? treasJ : null);
      setFxLocks(locksJ.items || []);
      setPartners(pj.partners || []);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
      setDashboard(null);
      setOperatingCountries([]);
      setCurrencies([]);
      setMethods([]);
      setMethodMatrix([]);
      setAliases([]);
      setInterfaces([]);
      setWallets([]);
      setCorridors([]);
      setFxRates([]);
      setCompliance([]);
      setFxAudit([]);
      setLockerPlayers([]);
      setEcosystemSegments([]);
      setPlayerRelations([]);
      setIntelDashboard(null);
      setReadiness([]);
      setInsights([]);
      setFxAlertRules([]);
      setFxAlertEvents([]);
      setSettlementSchedules([]);
      setPaymentRails([]);
      setTreasury(null);
      setFxLocks([]);
      setPartners([]);
    } finally {
      setLoading(false);
    }
  }, [token, headers]);

  useEffect(() => {
    void load();
  }, [load]);

  const onPricingPreview = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/pricing/preview`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          amount_cents: Number(pricingForm.amount_cents) || 0,
          player_code: pricingForm.player_code,
          country_code: pricingForm.country_code || undefined,
          payment_method_code: pricingForm.payment_method_code || undefined,
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setPricingResult(j);
      setOk(`Settlement ${j.settlement_cents} ${j.settlement_currency} · compliance ${j.compliance_status}`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/pricing/preview`));
    } finally {
      setLoading(false);
    }
  };

  const onAnalyzeIntelligence = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/money-intelligence/analyze`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(
        `Analyze: ${j.players_scored} players · ${j.insights_created} insights novos · readiness médio ${j.avg_readiness}.`,
      );
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/money-intelligence/analyze`));
    } finally {
      setLoading(false);
    }
  };

  const onFinanceSync = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/sync/finance-admin?trigger_finance_sync=true`, {
        method: "POST",
        headers,
      });
      const j = await r.json().catch(() => ({}));
      if (r.status === 404) {
        throw new Error(
          "Rota /sync/finance-admin nao encontrada. Recrie o container: cd 02_docker && docker compose up -d --build money_cambio_admin_service",
        );
      }
      if (!r.ok) throw new Error(parseError(j, "Finance Admin indisponivel (porta 8123) ou Money desatualizado."));
      setOk(
        `Sync Finance: ${j.players_created} criados, ${j.players_updated} atualizados, catálogo ${j.finance_catalog_total}.`,
      );
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/sync/finance-admin`));
    } finally {
      setLoading(false);
    }
  };

  const onSeed = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/seed`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Seed: ${JSON.stringify(j)}`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seed`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateCurrency = async () => {
    if (!canMutate || !currencyForm.code || !currencyForm.name) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/currencies`, { method: "POST", headers, body: JSON.stringify(currencyForm) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Moeda ${j.code} criada.`);
      setCurrencyForm({ code: "", name: "", symbol: "" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/currencies`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateMethod = async () => {
    if (!canMutate || !methodForm.code || !methodForm.name) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/payment-method-catalog`, { method: "POST", headers, body: JSON.stringify(methodForm) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Metodo ${j.code} criado.`);
      setMethodForm({ code: "", name: "" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/payment-method-catalog`));
    } finally {
      setLoading(false);
    }
  };

  const onUpsertFx = async () => {
    if (!canMutate) return;
    setLoading(true);
    try {
      const today = new Date().toISOString().slice(0, 10);
      const r = await fetch(`${API}/fx-rates`, {
        method: "POST",
        headers,
        body: JSON.stringify({ ...fxForm, rate_date: today }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`FX ${j.base_currency}/${j.quote_currency} @ ${j.rate_date}`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/fx-rates`));
    } finally {
      setLoading(false);
    }
  };

  const onConvert = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/fx-rates/convert`, {
        method: "POST",
        headers,
        body: JSON.stringify({ amount_cents: 10000, from_currency: fxForm.base_currency, to_currency: fxForm.quote_currency }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setConvertResult(j);
      setOk("Conversao calculada.");
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/fx-rates/convert`));
    } finally {
      setLoading(false);
    }
  };

  const onCreatePartner = async () => {
    if (!canMutate || !partnerForm.name || !partnerForm.code) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/integration-partners`, { method: "POST", headers, body: JSON.stringify(partnerForm) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Parceiro ${j.code} criado.`);
      setSelectedId(j.id);
      setPartnerForm({ name: "", code: "", partner_type: "FX_FEED" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/integration-partners`));
    } finally {
      setLoading(false);
    }
  };

  const onWebhook = async () => {
    if (!canMutate || !selectedId || !webhookUrl) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/integration-partners/${encodeURIComponent(selectedId)}/webhook`, {
        method: "PUT",
        headers,
        body: JSON.stringify({ url: webhookUrl, secret: webhookSecret || undefined, events: ["fx.updated", "money.catalog.changed"] }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Webhook configurado.");
    } catch (e) {
      setErr(normalizeNetworkError(e, "webhook"));
    } finally {
      setLoading(false);
    }
  };

  const onRotate = async () => {
    if (!canMutate || !selectedId) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/integration-partners/${encodeURIComponent(selectedId)}/api-keys/rotate`, {
        method: "POST",
        headers,
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setLastApiKey(j.api_key || "");
      setOk(`API key (${j.key_prefix}…). Copie agora.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, "api-keys/rotate"));
    } finally {
      setLoading(false);
    }
  };

  const overviewCards = dashboard
    ? [
        ["Moedas", String(dashboard.currencies)],
        ["Paises", String(dashboard.countries)],
        ["Metodos", String(dashboard.payment_methods)],
        ["Corredores", String(dashboard.corridors)],
        ["Taxas FX", String(dashboard.fx_rates)],
        ["Players ecossistema", String(dashboard.locker_players ?? 0)],
        ["Segmentos", String(dashboard.ecosystem_segments ?? 0)],
        ["Relacoes", String(dashboard.player_relations ?? 0)],
        ["Readiness médio", String(dashboard.avg_player_readiness ?? 0)],
        ["Insights abertos", String(dashboard.open_insights ?? 0)],
        ["Alertas FX", String(dashboard.open_fx_alerts ?? 0)],
        ["Prontidao", `${dashboard.readiness_grade} · ${dashboard.world_coverage_pct}% cobertura mundial`],
      ]
    : [];

  const filteredPlayers = useMemo(() => {
    if (!playerSegmentFilter) return lockerPlayers;
    return lockerPlayers.filter((x) => x.segment === playerSegmentFilter);
  }, [lockerPlayers, playerSegmentFilter]);

  const rows =
    tab === "countries"
        ? operatingCountries.map((x) => ({
            key: x.id,
            id: x.country_code,
            detalhe: `${x.name} · ${x.default_currency_code} · ${x.regulatory_zone} · redes: ${(x.locker_networks_json || []).join(", ") || "—"}`,
          }))
        : tab === "currencies"
          ? currencies.map((x) => ({ key: x.id, id: x.code, detalhe: `${x.name} · ${x.symbol || "—"}` }))
          : tab === "methods"
            ? methods.map((x) => ({ key: x.id, id: x.code, detalhe: x.name }))
            : tab === "matrix"
              ? methodMatrix.map((x) => ({
                  key: x.id,
                  id: `${x.country_code}/${x.payment_method_code}`,
                  detalhe: `min ${x.min_amount_cents} · instant ${x.is_instant_settlement ? "sim" : "nao"}`,
                }))
              : tab === "aliases"
                ? aliases.map((x) => ({
                    key: x.id,
                    id: x.ui_code,
                    detalhe: `${x.canonical_method_code} · ${x.default_payment_interface_code || "—"}`,
                  }))
                : tab === "interfaces"
                  ? interfaces.map((x) => ({ key: x.id, id: x.code, detalhe: x.name }))
                  : tab === "wallets"
                    ? wallets.map((x) => ({ key: x.id, id: x.code, detalhe: x.name }))
                    : tab === "corridors"
                      ? corridors.map((x) => ({
                          key: x.id,
                          id: x.corridor_code,
                          detalhe: `${x.origin_country_code}→${x.destination_country_code} · ${x.transaction_currency}→${x.settlement_currency} · spread ${x.default_spread_bps}bps`,
                        }))
                      : tab === "fx"
                        ? fxRates.map((x) => ({
                            key: x.id,
                            id: `${x.base_currency}/${x.quote_currency}`,
                            detalhe: `${x.rate} · ${x.rate_date} · ${x.source}`,
                          }))
                        : tab === "compliance"
                          ? compliance.map((x) => ({
                              key: x.id,
                              id: `${x.country_code}/${x.limit_type}`,
                              detalhe: `${x.amount_cents} ${x.currency_code} · ${x.description || ""}`,
                            }))
                          : tab === "audit"
                            ? fxAudit.map((x) => ({
                                key: x.id,
                                id: `${x.base_currency}/${x.quote_currency}`,
                                detalhe: `${x.old_rate ?? "—"} → ${x.new_rate} · ${x.rate_date}`,
                              }))
                            : tab === "players"
                              ? filteredPlayers.map((x) => ({
                                  key: x.id,
                                  id: x.player_code,
                                  detalhe: `${x.name} · ${x.segment} · Finance:${x.finance_catalog_code || "—"} · Fiscal:${x.fiscal_corridor_code || "—"}`,
                                }))
                              : tab === "segments"
                                ? ecosystemSegments.map((x) => ({
                                    key: x.code,
                                    id: x.code,
                                    detalhe: `${x.name} · ${x.player_count ?? 0} players · ${x.description || ""}`,
                                  }))
                                : tab === "relations"
                                  ? playerRelations.map((x) => ({
                                      key: x.id,
                                      id: `${x.from_player_code} → ${x.to_player_code}`,
                                      detalhe: `${x.relation_type} · ${x.notes || ""}`,
                                    }))
                                  : tab === "intelligence"
                                    ? [
                                        ...readiness.slice(0, 30).map((x) => ({
                                          key: x.player_code,
                                          id: `${x.player_code} · ${x.grade}`,
                                          detalhe: `score ${x.readiness_score} · fiscal ${x.fiscal_linked ? "sim" : "nao"} · FX ${x.fx_linked ? "sim" : "nao"}`,
                                        })),
                                        ...insights.slice(0, 20).map((x) => ({
                                          key: x.id,
                                          id: `[${x.severity}] ${x.title}`,
                                          detalhe: x.suggested_action || x.insight_type,
                                        })),
                                      ]
                                    : tab === "settlements"
                                      ? settlementSchedules.map((x) => ({
                                          key: x.id,
                                          id: `${x.scope_type}/${x.scope_code}`,
                                          detalhe: `${x.country_code} · T+${x.settlement_days} · cut ${x.cut_off_time_utc} UTC · ${x.settlement_currency}`,
                                        }))
                                      : tab === "rails"
                                        ? paymentRails.map((x) => ({
                                            key: x.id,
                                            id: `${x.player_code}/${x.country_code}`,
                                            detalhe: `${x.payment_method_code || "—"} · ${x.channel} · max ${x.max_amount_cents ?? "—"}`,
                                          }))
                                        : tab === "treasury"
                                          ? (treasury?.exposures || []).map((x) => ({
                                              key: x.currency_code,
                                              id: x.currency_code,
                                              detalhe: `${x.player_count} players · ${x.corridor_count} corredores · risco ${x.risk_hint} · FX ${x.has_fx_rate ? "ok" : "gap"}`,
                                            }))
                                          : tab === "fxlocks"
                                            ? fxLocks.map((x) => ({
                                                key: x.id,
                                                id: x.lock_reference,
                                                detalhe: `${x.corridor_code} · ${x.locked_rate} · expira ${x.expires_at}`,
                                              }))
                                            : partners.map((x) => ({
                                key: x.id,
                                id: x.code,
                                detalhe: `${x.name} · ${x.partner_type}`,
                              }));

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10, gap: 8 }}>
          <Link to="/ops/payment-gateway/admin" style={crossShortcutLinkStyle}>
            Payment Gateway
          </Link>
          <Link to="/ops/finance/admin?tab=fx" style={crossShortcutLinkStyle}>
            Finance FX
          </Link>
          <Link to="/ops/finance/admin?tab=networks" style={crossShortcutLinkStyle}>
            Finance redes
          </Link>
          <Link to="/ops/fiscal/admin?tab=corridors" style={crossShortcutLinkStyle}>
            Fiscal corredores
          </Link>
        </div>

        <OpsPageTitleHeader
          title="OPS — Money & Cambio"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Cobertura mundial: paises, matriz metodo×pais, corredores FX, compliance AML e auditoria de taxas —{" "}
          <code style={{ color: "#e2e8f0" }}>{API}</code>
        </p>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Dominio MONEY / CAMBIO</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {TAB_DEFS.map(([k, label]) => (
                <button key={k} type="button" style={tabButtonStyle(tab === k)} onClick={() => setTab(k)}>
                  {label}
                </button>
              ))}
            </div>
          </div>

          {tab === "currencies" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                code
                <input
                  value={currencyForm.code}
                  onChange={(e) => setCurrencyForm((f) => ({ ...f, code: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="BRL"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                name
                <input
                  value={currencyForm.name}
                  onChange={(e) => setCurrencyForm((f) => ({ ...f, name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                symbol
                <input
                  value={currencyForm.symbol}
                  onChange={(e) => setCurrencyForm((f) => ({ ...f, symbol: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
            </div>
          ) : null}

          {tab === "methods" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                code
                <input
                  value={methodForm.code}
                  onChange={(e) => setMethodForm((f) => ({ ...f, code: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                name
                <input
                  value={methodForm.name}
                  onChange={(e) => setMethodForm((f) => ({ ...f, name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
            </div>
          ) : null}

          {tab === "fx" ? (
            <>
              <div style={healthLocalFilterRowStyle}>
                <label style={healthLocalFilterFieldStyle}>
                  base
                  <input
                    value={fxForm.base_currency}
                    onChange={(e) => setFxForm((f) => ({ ...f, base_currency: e.target.value }))}
                    style={healthLocalFilterInputStyle}
                  />
                </label>
                <label style={healthLocalFilterFieldStyle}>
                  quote
                  <input
                    value={fxForm.quote_currency}
                    onChange={(e) => setFxForm((f) => ({ ...f, quote_currency: e.target.value }))}
                    style={healthLocalFilterInputStyle}
                  />
                </label>
                <label style={healthLocalFilterFieldStyle}>
                  rate
                  <input
                    value={fxForm.rate}
                    onChange={(e) => setFxForm((f) => ({ ...f, rate: e.target.value }))}
                    style={healthLocalFilterInputStyle}
                  />
                </label>
              </div>
              {convertResult ? (
                <p style={summary24hHintStyle}>
                  10000 centavos {convertResult.from_currency} → {convertResult.to_amount_cents}{" "}
                  {convertResult.to_currency}
                </p>
              ) : null}
            </>
          ) : null}

          {tab === "pricing" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                centavos
                <input
                  value={pricingForm.amount_cents}
                  onChange={(e) => setPricingForm((f) => ({ ...f, amount_cents: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                player
                <input
                  value={pricingForm.player_code}
                  onChange={(e) => setPricingForm((f) => ({ ...f, player_code: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                metodo
                <input
                  value={pricingForm.payment_method_code}
                  onChange={(e) => setPricingForm((f) => ({ ...f, payment_method_code: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <button type="button" style={buttonPrimaryStyle} onClick={() => void onPricingPreview()} disabled={loading}>
                Simular cotação
              </button>
            </div>
          ) : null}

          {tab === "players" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                segmento
                <select
                  value={playerSegmentFilter}
                  onChange={(e) => setPlayerSegmentFilter(e.target.value)}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="">Todos</option>
                  {ecosystemSegments.map((s) => (
                    <option key={s.code} value={s.code}>
                      {s.code} ({s.player_count ?? 0})
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ) : null}

          {tab === "partners" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                name
                <input
                  value={partnerForm.name}
                  onChange={(e) => setPartnerForm((f) => ({ ...f, name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                code
                <input
                  value={partnerForm.code}
                  onChange={(e) => setPartnerForm((f) => ({ ...f, code: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
            </div>
          ) : null}

          <div style={toolbarStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => void load()} disabled={loading || !token}>
              Atualizar
            </button>
            {canMutate ? (
              <>
                <button type="button" style={buttonGhostStyle} onClick={() => void onSeed()} disabled={loading}>
                  Seed
                </button>
                <button type="button" style={buttonGhostStyle} onClick={() => void onFinanceSync()} disabled={loading}>
                  Sync Finance
                </button>
                <button type="button" style={buttonGhostStyle} onClick={() => void onAnalyzeIntelligence()} disabled={loading}>
                  Analyze
                </button>
                {tab === "currencies" ? (
                  <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreateCurrency()} disabled={loading}>
                    Criar moeda
                  </button>
                ) : null}
                {tab === "methods" ? (
                  <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreateMethod()} disabled={loading}>
                    Criar metodo
                  </button>
                ) : null}
                {tab === "fx" ? (
                  <>
                    <button type="button" style={buttonPrimaryStyle} onClick={() => void onUpsertFx()} disabled={loading}>
                      Gravar taxa
                    </button>
                    <button type="button" style={buttonGhostStyle} onClick={() => void onConvert()} disabled={loading}>
                      Simular conversao
                    </button>
                  </>
                ) : null}
                {tab === "partners" ? (
                  <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreatePartner()} disabled={loading}>
                    Criar parceiro
                  </button>
                ) : null}
              </>
            ) : null}
          </div>
        </section>

        {tab === "partners" ? (
          <section style={opsSanityCardStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Webhook e API key</h3>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                partner
                <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} style={healthLocalFilterInputStyle}>
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
            </div>
            {canMutate ? (
              <div style={toolbarStyle}>
                <button type="button" style={buttonGhostStyle} onClick={() => void onWebhook()} disabled={!selectedId}>
                  Salvar webhook
                </button>
                <button type="button" style={buttonGhostStyle} onClick={() => void onRotate()} disabled={!selectedId}>
                  Rotacionar API key
                </button>
              </div>
            ) : null}
            {lastApiKey ? <pre style={apiKeyBannerStyle}>{lastApiKey}</pre> : null}
          </section>
        ) : null}

        {err ? <p style={{ color: "#f87171" }}>{err}</p> : null}
        {ok ? <p style={okBannerStyle}>{ok}</p> : null}

        {tab === "overview" ? (
          <>
            <section style={opsSanityCardStyle}>
              <div style={summary24hHeaderStyle}>
                <h3 style={{ margin: 0, fontSize: 14 }}>Visao global — Money &amp; Cambio</h3>
              </div>
              <p style={summary24hHintStyle}>KPIs do catalogo mundial (apos seed ou sync).</p>
              {overviewCards.length > 0 ? (
                <OverviewKpiGrid items={overviewCards} />
              ) : (
                <p style={mutedTextStyle}>Sem dados. Clique Seed ou Atualizar.</p>
              )}
            </section>
            {intelDashboard ? (
              <section style={{ ...opsSanityCardStyle, marginTop: 12 }}>
                <h3 style={{ margin: 0, fontSize: 14 }}>Money Intelligence</h3>
                <p style={summary24hHintStyle}>
                  Readiness médio {intelDashboard.avg_readiness} · insights {intelDashboard.open_insights} · alertas FX{" "}
                  {intelDashboard.open_fx_alerts}
                  {intelDashboard.top_gaps?.length ? ` · gaps: ${intelDashboard.top_gaps.slice(0, 2).join("; ")}` : ""}
                </p>
              </section>
            ) : null}
          </>
        ) : tab === "intelligence" ? (
          <>
            {intelDashboard ? (
              <OverviewKpiGrid
                items={[
                  ["Readiness médio", String(intelDashboard.avg_readiness)],
                  ["Insights abertos", String(intelDashboard.open_insights)],
                  ["Alertas FX", String(intelDashboard.open_fx_alerts)],
                  ["Regras FX", String(fxAlertRules.length)],
                  ["Corredores", String(intelDashboard.corridors_active)],
                ]}
              />
            ) : null}
            <table style={{ ...tableStyle, marginTop: 12 }}>
              <thead>
                <tr>
                  <th style={thStyle}>id</th>
                  <th style={thStyle}>detalhe</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.key}>
                    <td style={tdStyle}>{r.id}</td>
                    <td style={tdStyle}>{r.detalhe}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p style={summary24hHintStyle}>
              {readiness.length} readiness · {insights.length} insights · use Analyze para recalcular
            </p>
          </>
        ) : (
          <>
            {tab === "pricing" && pricingResult ? (
              <section style={{ ...opsSanityCardStyle, marginBottom: 12 }}>
                <p style={summary24hHintStyle}>
                  {pricingResult.settlement_cents} {pricingResult.settlement_currency} · spread {pricingResult.spread_bps}bps
                  + markup {pricingResult.markup_bps}bps · compliance {pricingResult.compliance_status}
                </p>
                <ul style={{ margin: 0, paddingLeft: 18, color: "#cbd5e1", fontSize: 13 }}>
                  {(pricingResult.lines || []).map((ln) => (
                    <li key={ln.label}>
                      {ln.label}: {ln.amount_cents ?? ""} {ln.currency ?? ""} {ln.detail || ""}
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
            {tab === "treasury" && treasury?.gaps?.length ? (
              <p style={summary24hHintStyle}>Gaps: {treasury.gaps.join(" · ")}</p>
            ) : null}
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>id</th>
                  <th style={thStyle}>detalhe</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.key}>
                    <td style={tdStyle}>{r.id}</td>
                    <td style={tdStyle}>{r.detalhe}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p style={summary24hHintStyle}>{rows.length} registro(s) · aba {tab}</p>
          </>
        )}
      </section>
    </div>
  );
}


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

const BASE = import.meta.env.VITE_ORDER_PICKUP_ADMIN_BASE_URL || "/api/opa";
const API = `${BASE}/v1/order-pickup-admin`;
const PAGE_VERSION = "ops/orders/admin v0.2";
const TABS = [
  "overview",
  "lookup",
  "orders",
  "items",
  "allocations",
  "channels",
  "food",
  "omnichannel",
  "warehouse",
  "manifests",
  "deadlines",
  "sla",
  "disputes",
  "returns",
  "notifications",
  "reconciliation",
  "holds",
  "substitutions",
  "gifts",
  "payments",
  "commissions",
  "credits",
  "partners",
  "integration",
];
const TAB_LABELS = {
  overview: "Hub",
  lookup: "360",
  orders: "Pedidos",
  items: "Itens",
  allocations: "Alocações",
  channels: "Players",
  food: "Food",
  omnichannel: "Omnichannel",
  warehouse: "CD",
  manifests: "Manifestos",
  deadlines: "Deadlines",
  sla: "SLA",
  disputes: "Disputas",
  returns: "Devoluções",
  notifications: "Notif.",
  reconciliation: "Pagamentos",
  holds: "Holds",
  substitutions: "Subst.",
  gifts: "Gift",
  payments: "Gateway",
  commissions: "Comissões",
  credits: "Créditos",
  partners: "Parceiros",
  integration: "Integração",
};

function parseError(payload, fallback = "Falha na API order-pickup-admin.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  return fallback;
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao (${endpoint}). Verifique proxy ${BASE} (porta 8018).`;
  }
  return raw;
}

function formatMoney(cents) {
  const n = Number(cents);
  if (!Number.isFinite(n)) return "—";
  return (n / 100).toFixed(2);
}

export default function OpsOrderPickupAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = TABS.includes(searchParams.get("tab") || "") ? searchParams.get("tab") : "overview";
  const setTab = (t) => setSearchParams({ tab: t }, { replace: true });
  const [partnerSubTab, setPartnerSubTab] = useState("ecommerce");
  const [ecItems, setEcItems] = useState([]);
  const [lgItems, setLgItems] = useState([]);
  const [orders, setOrders] = useState([]);
  const [pickups, setPickups] = useState([]);
  const [outbox, setOutbox] = useState([]);
  const [fulfillment, setFulfillment] = useState([]);
  const [credits, setCredits] = useState([]);
  const [orderItems, setOrderItems] = useState([]);
  const [pickupEvents, setPickupEvents] = useState([]);
  const [pickupTokens, setPickupTokens] = useState([]);
  const [pickupAttempts, setPickupAttempts] = useState([]);
  const [domainOutbox, setDomainOutbox] = useState([]);
  const [omnichannel, setOmnichannel] = useState([]);
  const [warehouseOrders, setWarehouseOrders] = useState([]);
  const [hubSummary, setHubSummary] = useState(null);
  const [allocations, setAllocations] = useState([]);
  const [manifests, setManifests] = useState([]);
  const [manifestItems, setManifestItems] = useState([]);
  const [channels, setChannels] = useState([]);
  const [worldReview, setWorldReview] = useState(null);
  const [channelFilter, setChannelFilter] = useState("");
  const [foodOrders, setFoodOrders] = useState([]);
  const [deadlines, setDeadlines] = useState([]);
  const [commissions, setCommissions] = useState([]);
  const [slaWatches, setSlaWatches] = useState([]);
  const [disputes, setDisputes] = useState([]);
  const [integrationHealth, setIntegrationHealth] = useState([]);
  const [lookupOrderId, setLookupOrderId] = useState("ord-seed-demo-001");
  const [order360, setOrder360] = useState(null);
  const [orderReturns, setOrderReturns] = useState([]);
  const [orderNotifications, setOrderNotifications] = useState([]);
  const [paymentRecon, setPaymentRecon] = useState([]);
  const [orderHolds, setOrderHolds] = useState([]);
  const [substitutions, setSubstitutions] = useState([]);
  const [giftPickups, setGiftPickups] = useState([]);
  const [paymentTxs, setPaymentTxs] = useState([]);
  const [partnerForm, setPartnerForm] = useState({ name: "", code: "" });
  const [omniForm, setOmniForm] = useState({
    order_id: "ord-seed-demo-001",
    store_id: "store-magalu-demo-01",
    pickup_type: "LOCKER_DELIVERY",
  });
  const [warehouseForm, setWarehouseForm] = useState({
    order_id: "ord-seed-demo-001",
    fulfillment_center_id: "fc-sp-001",
    carrier: "DHL",
  });
  const [creditForm, setCreditForm] = useState({
    order_id: "ord-seed-demo-001",
    user_id: "usr-demo",
    amount_cents: 500,
  });
  const [orderForm, setOrderForm] = useState({
    amount_cents: 4990,
    ecommerce_partner_id: "ec-ops-001",
    totem_id: "TOTEM-OPS",
  });
  const [selectedId, setSelectedId] = useState("");
  const [partnerType, setPartnerType] = useState("ECOMMERCE");
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
      const [ec, lg, ord, pk, cr, ob, ft, oi, pe, pt, pa, dom, omni, wh, hub, alloc, mf, mfi, ch, dl, comm, wrev, food, sla, disp, health, ret, notif, recon, holds, subs, gifts, paytx] = await Promise.all([
        fetch(`${API}/ecommerce-partners`, { headers }),
        fetch(`${API}/logistics-partners`, { headers }),
        fetch(`${API}/orders`, { headers }),
        fetch(`${API}/pickups`, { headers }),
        fetch(`${API}/credits`, { headers }),
        fetch(`${API}/integration-outbox`, { headers }),
        fetch(`${API}/fulfillment-tracking`, { headers }),
        fetch(`${API}/order-items`, { headers }),
        fetch(`${API}/pickup-events`, { headers }),
        fetch(`${API}/pickup-tokens`, { headers }),
        fetch(`${API}/pickup-attempts`, { headers }),
        fetch(`${API}/domain-event-outbox`, { headers }),
        fetch(`${API}/omnichannel-orders`, { headers }),
        fetch(`${API}/fulfillment-orders`, { headers }),
        fetch(`${API}/hub/summary`, { headers }),
        fetch(`${API}/allocations`, { headers }),
        fetch(`${API}/logistics-manifests`, { headers }),
        fetch(`${API}/logistics-manifests/items`, { headers }),
        fetch(`${API}/integration-channels`, { headers }),
        fetch(`${API}/lifecycle-deadlines`, { headers }),
        fetch(`${API}/marketplace-commissions`, { headers }),
        fetch(`${API}/integration-channels/world-review`, { headers }),
        fetch(`${API}/food-delivery-orders`, { headers }),
        fetch(`${API}/sla-watches`, { headers }),
        fetch(`${API}/order-disputes`, { headers }),
        fetch(`${API}/integration-health`, { headers }),
        fetch(`${API}/order-returns`, { headers }),
        fetch(`${API}/order-notifications`, { headers }),
        fetch(`${API}/payment-reconciliation`, { headers }),
        fetch(`${API}/order-holds`, { headers }),
        fetch(`${API}/item-substitutions`, { headers }),
        fetch(`${API}/gift-pickups`, { headers }),
        fetch(`${API}/payment-transactions`, { headers }),
      ]);
      const ecJson = await ec.json().catch(() => ({}));
      const lgJson = await lg.json().catch(() => ({}));
      const ordJson = await ord.json().catch(() => ({}));
      const pkJson = await pk.json().catch(() => ({}));
      const crJson = await cr.json().catch(() => ({}));
      const obJson = await ob.json().catch(() => ({}));
      const ftJson = await ft.json().catch(() => ({}));
      const oiJson = await oi.json().catch(() => ({}));
      const peJson = await pe.json().catch(() => ({}));
      const ptJson = await pt.json().catch(() => ({}));
      const paJson = await pa.json().catch(() => ({}));
      const domJson = await dom.json().catch(() => ({}));
      const omniJson = await omni.json().catch(() => ({}));
      const whJson = await wh.json().catch(() => ({}));
      const hubJson = await hub.json().catch(() => ({}));
      const allocJson = await alloc.json().catch(() => ({}));
      const mfJson = await mf.json().catch(() => ({}));
      const mfiJson = await mfi.json().catch(() => ({}));
      const chJson = await ch.json().catch(() => ({}));
      const dlJson = await dl.json().catch(() => ({}));
      const commJson = await comm.json().catch(() => ({}));
      const wrevJson = await wrev.json().catch(() => ({}));
      const foodJson = await food.json().catch(() => ({}));
      const slaJson = await sla.json().catch(() => ({}));
      const dispJson = await disp.json().catch(() => ({}));
      const healthJson = await health.json().catch(() => ({}));
      const retJson = await ret.json().catch(() => ({}));
      const notifJson = await notif.json().catch(() => ({}));
      const reconJson = await recon.json().catch(() => ({}));
      const holdsJson = await holds.json().catch(() => ({}));
      const subsJson = await subs.json().catch(() => ({}));
      const giftsJson = await gifts.json().catch(() => ({}));
      const paytxJson = await paytx.json().catch(() => ({}));
      if (!ec.ok) throw new Error(parseError(ecJson));
      if (!lg.ok) throw new Error(parseError(lgJson));
      if (!ord.ok) throw new Error(parseError(ordJson));
      if (!pk.ok) throw new Error(parseError(pkJson));
      if (!cr.ok) throw new Error(parseError(crJson));
      if (!ob.ok) throw new Error(parseError(obJson));
      if (!ft.ok) throw new Error(parseError(ftJson));
      if (!oi.ok) throw new Error(parseError(oiJson));
      if (!pe.ok) throw new Error(parseError(peJson));
      if (!pt.ok) throw new Error(parseError(ptJson));
      if (!pa.ok) throw new Error(parseError(paJson));
      if (!dom.ok) throw new Error(parseError(domJson));
      if (!omni.ok) throw new Error(parseError(omniJson));
      if (!wh.ok) throw new Error(parseError(whJson));
      if (!hub.ok) throw new Error(parseError(hubJson));
      if (!alloc.ok) throw new Error(parseError(allocJson));
      if (!mf.ok) throw new Error(parseError(mfJson));
      if (!mfi.ok) throw new Error(parseError(mfiJson));
      if (!ch.ok) throw new Error(parseError(chJson));
      if (!dl.ok) throw new Error(parseError(dlJson));
      if (!comm.ok) throw new Error(parseError(commJson));
      if (!wrev.ok) throw new Error(parseError(wrevJson));
      if (!food.ok) throw new Error(parseError(foodJson));
      if (!sla.ok) throw new Error(parseError(slaJson));
      if (!disp.ok) throw new Error(parseError(dispJson));
      if (!health.ok) throw new Error(parseError(healthJson));
      if (!ret.ok) throw new Error(parseError(retJson));
      if (!notif.ok) throw new Error(parseError(notifJson));
      if (!recon.ok) throw new Error(parseError(reconJson));
      if (!holds.ok) throw new Error(parseError(holdsJson));
      if (!subs.ok) throw new Error(parseError(subsJson));
      if (!gifts.ok) throw new Error(parseError(giftsJson));
      if (!paytx.ok) throw new Error(parseError(paytxJson));
      setEcItems(ecJson.partners || []);
      setLgItems(lgJson.partners || []);
      setOrders(ordJson.items || []);
      setPickups(pkJson.items || []);
      setCredits(crJson.items || []);
      setOutbox(obJson.items || []);
      setFulfillment(ftJson.items || []);
      setOrderItems(oiJson.items || []);
      setPickupEvents(peJson.items || []);
      setPickupTokens(ptJson.items || []);
      setPickupAttempts(paJson.items || []);
      setDomainOutbox(domJson.items || []);
      setOmnichannel(omniJson.items || []);
      setWarehouseOrders(whJson.items || []);
      setHubSummary(hubJson);
      setAllocations(allocJson.items || []);
      setManifests(mfJson.items || []);
      setManifestItems(mfiJson.items || []);
      setChannels(chJson.items || []);
      setDeadlines(dlJson.items || []);
      setCommissions(commJson.items || []);
      setWorldReview(wrevJson);
      setFoodOrders(foodJson.items || []);
      setSlaWatches(slaJson.items || []);
      setDisputes(dispJson.items || []);
      setIntegrationHealth(healthJson.items || []);
      setOrderReturns(retJson.items || []);
      setOrderNotifications(notifJson.items || []);
      setPaymentRecon(reconJson.items || []);
      setOrderHolds(holdsJson.items || []);
      setSubstitutions(subsJson.items || []);
      setGiftPickups(giftsJson.items || []);
      setPaymentTxs(paytxJson.items || []);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
      setEcItems([]);
      setLgItems([]);
      setOrders([]);
      setPickups([]);
      setCredits([]);
      setOutbox([]);
      setFulfillment([]);
      setOrderItems([]);
      setPickupEvents([]);
      setPickupTokens([]);
      setPickupAttempts([]);
      setDomainOutbox([]);
    } finally {
      setLoading(false);
    }
  }, [token, headers]);

  const onSeed = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seed`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Seed aplicado (parceiros, pedido demo, outbox).");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seed`));
    } finally {
      setLoading(false);
    }
  };

  const onSyncWorldPlayers = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/integration-channels/sync-world-players`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(
        `Players mundiais sincronizados: ${j.channels_created ?? 0} canais novos, ${j.ecommerce ?? 0} EC, ${j.logistics ?? 0} LG.`,
      );
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/integration-channels/sync-world-players`));
    } finally {
      setLoading(false);
    }
  };

  const onCreatePartner = async () => {
    if (!token || !canMutate || !partnerForm.name || !partnerForm.code) return;
    const path = partnerSubTab === "ecommerce" ? "ecommerce-partners" : "logistics-partners";
    setLoading(true);
    setErr("");
    try {
      const body =
        partnerSubTab === "ecommerce"
          ? { ...partnerForm, integration_type: "REST", status: "ACTIVE" }
          : { ...partnerForm, integration_type: "REST" };
      const r = await fetch(`${API}/${path}`, { method: "POST", headers, body: JSON.stringify(body) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Parceiro ${j.code} criado.`);
      setSelectedId(j.id);
      setPartnerType(partnerSubTab === "ecommerce" ? "ECOMMERCE" : "LOGISTICS");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/${path}`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateCredit = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/credits`, {
        method: "POST",
        headers,
        body: JSON.stringify({ ...creditForm, type: "GOODWILL", currency: "BRL", status: "AVAILABLE" }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Crédito criado.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/credits`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateOmnichannel = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/omnichannel-orders`, {
        method: "POST",
        headers,
        body: JSON.stringify({ ...omniForm, status: "PENDING" }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Omnichannel ${j.id} criado.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/omnichannel-orders`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateWarehouse = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/fulfillment-orders`, {
        method: "POST",
        headers,
        body: JSON.stringify({ ...warehouseForm, status: "PENDING" }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Fulfillment CD ${j.id} criado.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/fulfillment-orders`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateOrder = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/orders`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          channel: "KIOSK",
          region: "BR",
          totem_id: orderForm.totem_id,
          amount_cents: Number(orderForm.amount_cents),
          currency: "BRL",
          status: "PENDING",
          payment_status: "PENDING",
          ecommerce_partner_id: orderForm.ecommerce_partner_id || undefined,
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Pedido ${j.id} criado.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/orders`));
    } finally {
      setLoading(false);
    }
  };

  const onWebhook = async () => {
    if (!token || !canMutate || !selectedId || !webhookUrl) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(
        `${API}/partners/${encodeURIComponent(selectedId)}/webhook?partner_type=${partnerType}`,
        {
          method: "PUT",
          headers,
          body: JSON.stringify({
            url: webhookUrl,
            secret: webhookSecret || undefined,
            events: ["ORDER_PAID", "ORDER_PICKED_UP", "ORDER_EXPIRED"],
          }),
        },
      );
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
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
      const r = await fetch(
        `${API}/partners/${encodeURIComponent(selectedId)}/api-keys/rotate?partner_type=${partnerType}`,
        { method: "POST", headers },
      );
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setLastApiKey(j.api_key || "");
      setOk(`Nova API key (${j.key_prefix}…). Copie agora.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/partners/.../api-keys/rotate`));
    } finally {
      setLoading(false);
    }
  };

  const onReplayDomain = async (outboxId) => {
    if (!token || !canMutate || !outboxId) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/domain-event-outbox/${encodeURIComponent(outboxId)}/replay`, {
        method: "POST",
        headers,
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Domain outbox ${outboxId} reenfileirado.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, "domain-replay"));
    } finally {
      setLoading(false);
    }
  };

  const onReplay = async (outboxId) => {
    if (!token || !canMutate || !outboxId) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/integration-outbox/${encodeURIComponent(outboxId)}/replay`, {
        method: "POST",
        headers,
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Outbox ${outboxId} reenfileirado.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/integration-outbox/.../replay`));
    } finally {
      setLoading(false);
    }
  };

  const partnerItems = partnerType === "ECOMMERCE" ? ecItems : lgItems;

  useEffect(() => {
    void load();
  }, [load]);

  const onLookup360 = async () => {
    if (!token || !lookupOrderId.trim()) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/orders/${encodeURIComponent(lookupOrderId.trim())}/360`, { headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOrder360(j);
      setOk(`Order 360 · health ${j.health_score}`);
    } catch (e) {
      setOrder360(null);
      setErr(normalizeNetworkError(e, `${API}/orders/.../360`));
    } finally {
      setLoading(false);
    }
  };

  const onSyncSla = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/sla-watches/sync`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`SLA: +${j.created} criados, ${j.breached} violados`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/sla-watches/sync`));
    } finally {
      setLoading(false);
    }
  };

  const tableRows =
    tab === "overview" || tab === "lookup"
      ? []
      : tab === "omnichannel"
        ? omnichannel.map((x) => ({
            key: `omni-${x.id}`,
            tipo: "omnichannel",
            id: x.id,
            detalhe: `${x.store_id} · ${x.pickup_type} · ${x.status} · order ${x.order_id}`,
          }))
        : tab === "warehouse"
          ? warehouseOrders.map((x) => ({
              key: `wh-${x.id}`,
              tipo: "fulfillment_cd",
              id: x.id,
              detalhe: `${x.status} · ${x.carrier || "—"} · ${x.tracking_code || "—"} · order ${x.order_id}`,
            }))
          : tab === "allocations"
            ? allocations.map((x) => ({
                key: `alloc-${x.id}`,
                tipo: "allocation",
                id: x.id,
                detalhe: `slot ${x.slot} · ${x.state} · order ${x.order_id}`,
              }))
            : tab === "manifests"
              ? [
                  ...manifests.map((x) => ({
                    key: `mf-${x.id}`,
                    tipo: "manifest",
                    id: x.id,
                    detalhe: `${x.status} · ${x.locker_id}`,
                  })),
                  ...manifestItems.map((x) => ({
                    key: `mfi-${x.id}`,
                    tipo: "parcel",
                    id: x.tracking_code,
                    detalhe: `${x.status} · mf ${x.manifest_id}`,
                  })),
                ]
                : tab === "food"
                  ? foodOrders.map((x) => ({
                      key: `fd-${x.id}`,
                      tipo: "food",
                      id: x.platform_code,
                      detalhe: `${x.status} · ${x.temperature_zone} · order ${x.order_id}`,
                    }))
                  : tab === "channels"
                ? (channelFilter
                    ? channels.filter(
                        (c) => c.code.includes(channelFilter.toUpperCase()) || c.player_type === channelFilter,
                      )
                    : channels
                  ).map((x) => ({
                    key: `ch-${x.id}`,
                    tipo: x.player_type,
                    id: x.code,
                    detalhe: `${x.name} · ${x.country} · ${x.review_status || "—"} · ${(x.markets || []).join("/")}`,
                  }))
                : tab === "items"
                  ? orderItems.map((i) => ({
                      key: `oi-${i.id}`,
                      tipo: "item",
                      id: i.sku_id,
                      detalhe: `order ${i.order_id} · qty ${i.quantity}`,
                    }))
                  : tab === "deadlines"
                    ? deadlines.map((x) => ({
                        key: `dl-${x.id}`,
                        tipo: "deadline",
                        id: x.deadline_type,
                        detalhe: `${x.status} · order ${x.order_id}`,
                      }))
                    : tab === "sla"
                      ? slaWatches.map((x) => ({
                          key: `sla-${x.id}`,
                          tipo: x.watch_type,
                          id: x.order_id,
                          detalhe: `${x.status} · due ${x.due_at}`,
                        }))
                      : tab === "disputes"
                        ? disputes.map((x) => ({
                            key: `disp-${x.id}`,
                            tipo: x.dispute_type,
                            id: x.id,
                            detalhe: `${x.status} · order ${x.order_id}`,
                          }))
                        : tab === "returns"
                          ? orderReturns.map((x) => ({
                              key: `ret-${x.id}`,
                              tipo: x.return_type,
                              id: x.order_id,
                              detalhe: `${x.status} · ${x.reason_code || "—"}`,
                            }))
                          : tab === "notifications"
                            ? orderNotifications.map((x) => ({
                                key: `ntf-${x.id}`,
                                tipo: x.channel,
                                id: x.template_code,
                                detalhe: `${x.status} · order ${x.order_id}`,
                              }))
                            : tab === "reconciliation"
                              ? paymentRecon.map((x) => ({
                                  key: `rec-${x.id}`,
                                  tipo: x.status,
                                  id: x.order_id,
                                  detalhe: `esp ${x.expected_cents} cap ${x.captured_cents}`,
                                }))
                              : tab === "substitutions"
                                ? substitutions.map((x) => ({
                                    key: `sub-${x.id}`,
                                    tipo: x.reason_code,
                                    id: x.order_id,
                                    detalhe: `${x.status} · ${x.original_sku_id} → ${x.substitute_sku_id}`,
                                  }))
                                : tab === "gifts"
                                  ? giftPickups.map((x) => ({
                                      key: `gift-${x.id}`,
                                      tipo: "gift",
                                      id: x.order_id,
                                      detalhe: `${x.status} · ${x.recipient_name} · ${x.pickup_authorization_code || "—"}`,
                                    }))
                                  : tab === "payments"
                                    ? paymentTxs.map((x) => ({
                                        key: `ptx-${x.id}`,
                                        tipo: x.gateway,
                                        id: x.order_id,
                                        detalhe: `${x.status} · ${x.amount_cents} · ${x.source}`,
                                      }))
                                    : tab === "holds"
                                ? orderHolds.map((x) => ({
                                    key: `hold-${x.id}`,
                                    tipo: x.hold_type,
                                    id: x.order_id,
                                    detalhe: `${x.status} · ${x.reason || "—"}`,
                                  }))
                                : tab === "commissions"
                      ? commissions.map((x) => ({
                          key: `mc-${x.id}`,
                          tipo: "commission",
                          id: x.id,
                          detalhe: `${x.status} · order ${x.order_id} · R$ ${formatMoney(x.commission_amount_cents)}`,
                        }))
                      : tab === "partners"
      ? [
          ...ecItems.map((p) => ({
            key: `ec-${p.id}`,
            tipo: "EC",
            id: p.code,
            detalhe: `${p.name} · ${p.status || "—"} · ${p.active ? "ativo" : "inativo"}`,
          })),
          ...lgItems.map((p) => ({
            key: `lg-${p.id}`,
            tipo: "LG",
            id: p.code,
            detalhe: `${p.name} · ${p.active ? "ativo" : "inativo"}`,
          })),
        ]
      : tab === "orders"
        ? [
            ...orders.map((o) => ({
              key: `ord-${o.id}`,
              tipo: "order",
              id: o.id,
              detalhe: `${o.status} / ${o.payment_status} · R$ ${formatMoney(o.amount_cents)} · partner ${o.ecommerce_partner_id || "—"}`,
            })),
            ...pickups.map((p) => ({
              key: `pkp-${p.id}`,
              tipo: "pickup",
              id: p.id,
              detalhe: `${p.status} · ${p.lifecycle_stage} · order ${p.order_id}`,
            })),
          ]
        : tab === "credits"
          ? credits.map((c) => ({
              key: `crd-${c.id}`,
              tipo: "credit",
              id: c.id,
              detalhe: `${c.type} · ${c.status} · R$ ${formatMoney(c.amount_cents)} · order ${c.order_id}`,
            }))
          : [
              ...integrationHealth.map((x) => ({
                key: `ih-${x.id}`,
                tipo: "health",
                id: x.channel_code,
                detalhe: `${x.check_type} · ${x.status} · ${x.latency_ms ?? "—"}ms`,
              })),
              ...outbox.map((x) => ({
                key: `pob-${x.id}`,
                tipo: "partner_outbox",
                id: x.id,
                detalhe: `${x.event_type} · ${x.status} · order ${x.order_id}`,
                replayKind: "partner",
                replayId: x.id,
              })),
              ...domainOutbox.map((x) => ({
                key: `dob-${x.id}`,
                tipo: "domain_outbox",
                id: x.id,
                detalhe: `${x.event_name || "—"} · ${x.status} · ${x.aggregate_id || "—"}`,
                replayKind: "domain",
                replayId: x.id,
              })),
              ...pickupEvents.map((x) => ({
                key: `pe-${x.id}`,
                tipo: "pickup_event",
                id: x.id,
                detalhe: `${x.event_type} · pickup ${x.pickup_id}`,
              })),
              ...pickupTokens.map((x) => ({
                key: `pt-${x.id}`,
                tipo: "token",
                id: x.id,
                detalhe: `order ${x.order_id} · ${x.is_active ? "ativo" : "inativo"}`,
              })),
              ...pickupAttempts.map((x) => ({
                key: `pa-${x.id}`,
                tipo: "attempt",
                id: x.id,
                detalhe: `order ${x.order_id} · ${x.ok ? "ok" : "fail"}`,
              })),
              ...fulfillment.map((x) => ({
                key: `ft-${x.id}`,
                tipo: "fulfillment",
                id: x.order_id,
                detalhe: `${x.fulfillment_type} · ${x.status}`,
              })),
            ];

  const listCount = tableRows.length;

  const listTitle =
    tab === "overview"
      ? "Hub pedidos — KPIs"
      : tab === "partners"
        ? `Parceiros (e-commerce: ${ecItems.length}, logística: ${lgItems.length})`
        : tab === "orders"
          ? `Pedidos (${orders.length}) · pickups (${pickups.length}) · itens (${orderItems.length})`
          : tab === "omnichannel"
            ? `Omnichannel (${omnichannel.length})`
            : tab === "warehouse"
              ? `Fulfillment CD (${warehouseOrders.length})`
              : tab === "credits"
                ? `Créditos (${credits.length})`
                : `Integração (partner outbox: ${outbox.length}, domain: ${domainOutbox.length}, events: ${pickupEvents.length})`;

  return (
    <div style={pageStyle} data-testid="ops-order-pickup-admin-page">
      <section style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10, gap: 8 }}>
          <Link to="/ops/tenants/admin" style={crossShortcutLinkStyle}>
            Tenants
          </Link>
          <Link to="/ops/partners/admin" style={crossShortcutLinkStyle}>
            Parceiros
          </Link>
          <Link to="/ops/payment-gateway/admin" style={crossShortcutLinkStyle}>
            Payment Gateway
          </Link>
          <Link to="/ops/access/user-roles" style={crossShortcutLinkStyle}>
            user_roles
          </Link>
          <Link to="/ops/order/pickup-health" style={crossShortcutLinkStyle}>
            Pickup health
          </Link>
          <Link to="/ops/order/executive-summary" style={crossShortcutLinkStyle}>
            Executive summary
          </Link>
        </div>

        <OpsPageTitleHeader
          title="OPS — Pedidos"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Hub pedidos: omnichannel, fulfillment CD, parceiros, outbox e credits — <code style={{ color: "#e2e8f0" }}>{API}</code> — role{" "}
          <code style={{ color: "#e2e8f0" }}>admin_operacao</code> para escrita.
        </p>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Área de cadastro</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {TABS.map((t) => (
                <button key={t} type="button" style={tabButtonStyle(tab === t)} onClick={() => setTab(t)}>
                  {TAB_LABELS[t] || t}
                </button>
              ))}
            </div>
          </div>

          {tab === "overview" && hubSummary ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 10 }}>
              {[
                ["Pedidos", hubSummary.orders],
                ["Pickups", hubSummary.pickups],
                ["Outbox parceiro", hubSummary.partner_outbox_pending],
                ["Domain outbox", hubSummary.domain_outbox_pending],
                ["Omnichannel", hubSummary.omnichannel],
                ["Fulfillment CD", hubSummary.fulfillment_orders],
                ["Tracking", hubSummary.fulfillment_tracking],
                ["Créditos", hubSummary.credits],
                ["Alocações", hubSummary.allocations],
                ["Manifestos", hubSummary.logistics_manifests],
                ["Players", hubSummary.integration_channels],
                ["Comissões", hubSummary.marketplace_commissions],
                ["Deadlines", hubSummary.lifecycle_deadlines_pending],
                ["Timeline", hubSummary.timeline_events],
                ["SLA ativos", hubSummary.sla_watches_active],
                ["SLA violados", hubSummary.sla_watches_breached],
                ["Disputas", hubSummary.disputes_open],
                ["Devoluções", hubSummary.returns_open],
                ["Recon diverg.", hubSummary.payment_recon_mismatch],
                ["Holds", hubSummary.ops_holds_active],
                ["Notificações", hubSummary.notifications_sent],
              ].map(([label, value]) => (
                <div key={label} style={{ ...cardStyle, padding: 12 }}>
                  <div style={{ fontSize: 11, color: "#94a3b8" }}>{label}</div>
                  <div style={{ fontSize: 22, fontWeight: 700 }}>{value}</div>
                </div>
              ))}
            </div>
          ) : null}

          {tab === "lookup" ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <div style={healthLocalFilterRowStyle}>
                <label style={healthLocalFilterFieldStyle}>
                  order_id
                  <input
                    value={lookupOrderId}
                    onChange={(e) => setLookupOrderId(e.target.value)}
                    style={healthLocalFilterInputStyle}
                  />
                </label>
                <button type="button" style={buttonPrimaryStyle} onClick={() => void onLookup360()}>
                  Buscar 360
                </button>
              </div>
              {order360 ? (
                <div style={{ ...cardStyle, padding: 12, fontSize: 13 }}>
                  <div>
                    Health: <strong>{order360.health_score}</strong> · riscos: {(order360.risk_flags || []).join(", ") || "—"}
                  </div>
                  <ul style={{ margin: "8px 0 0", paddingLeft: 18, color: "#94a3b8" }}>
                    {(order360.timeline || []).slice(0, 12).map((ev) => (
                      <li key={ev.id}>
                        [{ev.severity}] {ev.title} · {ev.occurred_at}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ) : null}

          {tab === "sla" ? (
            <button type="button" style={buttonGhostStyle} onClick={() => void onSyncSla()} disabled={!canMutate}>
              Sincronizar SLA
            </button>
          ) : null}

          {tab === "partners" ? (
            <>
              <div style={summary24hHeaderStyle}>
                <span style={{ fontSize: 13, color: "#94a3b8" }}>Tipo de parceiro</span>
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    type="button"
                    style={tabButtonStyle(partnerSubTab === "ecommerce")}
                    onClick={() => setPartnerSubTab("ecommerce")}
                  >
                    E-commerce
                  </button>
                  <button
                    type="button"
                    style={tabButtonStyle(partnerSubTab === "logistics")}
                    onClick={() => setPartnerSubTab("logistics")}
                  >
                    Logística
                  </button>
                </div>
              </div>
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
            </>
          ) : null}

          {tab === "orders" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                amount_cents
                <input
                  type="number"
                  min={0}
                  value={orderForm.amount_cents}
                  onChange={(e) => setOrderForm((f) => ({ ...f, amount_cents: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                ecommerce_partner_id
                <input
                  value={orderForm.ecommerce_partner_id}
                  onChange={(e) => setOrderForm((f) => ({ ...f, ecommerce_partner_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                totem_id
                <input
                  value={orderForm.totem_id}
                  onChange={(e) => setOrderForm((f) => ({ ...f, totem_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
            </div>
          ) : null}

          {tab === "omnichannel" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                order_id
                <input
                  value={omniForm.order_id}
                  onChange={(e) => setOmniForm((f) => ({ ...f, order_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                store_id
                <input
                  value={omniForm.store_id}
                  onChange={(e) => setOmniForm((f) => ({ ...f, store_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                pickup_type
                <select
                  value={omniForm.pickup_type}
                  onChange={(e) => setOmniForm((f) => ({ ...f, pickup_type: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="LOCKER_DELIVERY">LOCKER_DELIVERY</option>
                  <option value="STORE_PICKUP">STORE_PICKUP</option>
                  <option value="HOME_DELIVERY">HOME_DELIVERY</option>
                </select>
              </label>
            </div>
          ) : null}

          {tab === "warehouse" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                order_id
                <input
                  value={warehouseForm.order_id}
                  onChange={(e) => setWarehouseForm((f) => ({ ...f, order_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                fulfillment_center_id
                <input
                  value={warehouseForm.fulfillment_center_id}
                  onChange={(e) => setWarehouseForm((f) => ({ ...f, fulfillment_center_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                carrier
                <input
                  value={warehouseForm.carrier}
                  onChange={(e) => setWarehouseForm((f) => ({ ...f, carrier: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
            </div>
          ) : null}

          {tab === "credits" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                order_id
                <input
                  value={creditForm.order_id}
                  onChange={(e) => setCreditForm((f) => ({ ...f, order_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                user_id
                <input
                  value={creditForm.user_id}
                  onChange={(e) => setCreditForm((f) => ({ ...f, user_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                amount_cents
                <input
                  type="number"
                  min={1}
                  value={creditForm.amount_cents}
                  onChange={(e) => setCreditForm((f) => ({ ...f, amount_cents: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
            </div>
          ) : null}

          {tab === "channels" ? (
            <>
              {worldReview ? (
                <p style={{ ...summary24hHintStyle, margin: "0 0 8px" }}>
                  Catálogo {worldReview.catalog_configured}/{worldReview.catalog_total} · P3{" "}
                  {worldReview.prompt3_configured}/{worldReview.prompt3_total} · P4{" "}
                  {worldReview.prompt4_configured}/{worldReview.prompt4_total}
                </p>
              ) : null}
              <div style={healthLocalFilterRowStyle}>
                <select
                  value={channelFilter}
                  onChange={(e) => setChannelFilter(e.target.value)}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="">Todos</option>
                  <option value="MARKETPLACE">MARKETPLACE</option>
                  <option value="COLLECTION_POINT">COLLECTION_POINT</option>
                  <option value="LOCKER_NETWORK">LOCKER_NETWORK</option>
                  <option value="CARRIER">CARRIER</option>
                  <option value="AGGREGATOR">AGGREGATOR</option>
                  <option value="FOOD_DELIVERY">FOOD_DELIVERY</option>
                </select>
              </div>
            </>
          ) : null}

          {tab === "integration" ? (
            <p style={summary24hHintStyle}>
              Outbox parceiro/domain, eventos de pickup, tokens, tentativas e fulfillment.
            </p>
          ) : null}

          <div style={toolbarStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => void load()} disabled={loading || !token}>
              {loading ? "Atualizando..." : "Listar"}
            </button>
            {canMutate ? (
              <>
                <button type="button" style={buttonGhostStyle} onClick={() => void onSeed()} disabled={loading}>
                  Seed
                </button>
                {tab === "partners" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreatePartner()}
                    disabled={loading || !partnerForm.name || !partnerForm.code}
                  >
                    Criar {partnerSubTab === "ecommerce" ? "e-commerce" : "logística"}
                  </button>
                ) : null}
                {tab === "orders" ? (
                  <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreateOrder()} disabled={loading}>
                    Criar pedido
                  </button>
                ) : null}
                {tab === "omnichannel" ? (
                  <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreateOmnichannel()} disabled={loading}>
                    Criar omnichannel
                  </button>
                ) : null}
                {tab === "warehouse" ? (
                  <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreateWarehouse()} disabled={loading}>
                    Criar fulfillment CD
                  </button>
                ) : null}
                {tab === "channels" ? (
                  <button type="button" style={buttonPrimaryStyle} onClick={() => void onSyncWorldPlayers()} disabled={loading}>
                    Sync players mundiais
                  </button>
                ) : null}
                {tab === "credits" ? (
                  <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreateCredit()} disabled={loading}>
                    Criar crédito
                  </button>
                ) : null}
              </>
            ) : null}
          </div>
        </section>

        {tab === "partners" ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Webhook e API key</h3>
            </div>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                partner_type
                <select value={partnerType} onChange={(e) => setPartnerType(e.target.value)} style={healthLocalFilterInputStyle}>
                  <option value="ECOMMERCE">ECOMMERCE</option>
                  <option value="LOGISTICS">LOGISTICS</option>
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                partner_id
                <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} style={healthLocalFilterInputStyle}>
                  <option value="">— selecione —</option>
                  {partnerItems.map((p) => (
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
                secret (opcional)
                <input value={webhookSecret} onChange={(e) => setWebhookSecret(e.target.value)} style={healthLocalFilterInputStyle} />
              </label>
            </div>
            <div style={toolbarStyle}>
              <button
                type="button"
                style={buttonGhostStyle}
                onClick={() => void onWebhook()}
                disabled={!canMutate || !selectedId || !webhookUrl}
              >
                Salvar webhook
              </button>
              <button type="button" style={buttonGhostStyle} onClick={() => void onRotate()} disabled={!canMutate || !selectedId}>
                Rotacionar API key
              </button>
            </div>
            {lastApiKey ? (
              <p style={apiKeyBannerStyle}>
                API key: <code>{lastApiKey}</code>
              </p>
            ) : null}
          </section>
        ) : null}

        {err ? (
          <div style={criticalBannerStyle} role="alert">
            {err}
          </div>
        ) : null}
        {ok ? <p style={okBannerStyle}>{ok}</p> : null}
        {!token ? <p style={summary24hHintStyle}>Faca login com perfil admin_operacao.</p> : null}
        {token && !canMutate ? <p style={summary24hHintStyle}>Escrita exige admin_operacao.</p> : null}

        {listCount > 0 ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>{listTitle}</h3>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["tipo", "code / id", "detalhe", ...(tab === "integration" ? ["acao"] : [])].map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tableRows.map((row) => (
                    <tr key={row.key}>
                      <td style={tdStyle}>{row.tipo}</td>
                      <td style={tdStyle}>
                        <code>{row.id}</code>
                      </td>
                      <td style={tdStyle}>{row.detalhe}</td>
                      {tab === "integration" ? (
                        <td style={tdStyle}>
                          {row.replayId && canMutate ? (
                            <button
                              type="button"
                              style={buttonGhostStyle}
                              onClick={() =>
                                void (row.replayKind === "domain"
                                  ? onReplayDomain(row.replayId)
                                  : onReplay(row.replayId))
                              }
                              disabled={loading}
                            >
                              Replay
                            </button>
                          ) : (
                            "—"
                          )}
                        </td>
                      ) : null}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : token && !loading ? (
          <p style={summary24hHintStyle}>Nenhum registro. Use Listar ou Seed (admin_operacao).</p>
        ) : null}
      </section>
    </div>
  );
}

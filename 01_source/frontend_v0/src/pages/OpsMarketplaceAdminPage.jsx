
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

const BASE = import.meta.env.VITE_MARKETPLACE_ADMIN_BASE_URL || "/api/mka";
const API = `${BASE}/v1/marketplace-admin`;
const PAGE_VERSION = "ops/marketplace/admin v0.2";

const TAB_ITEMS = [
  { id: "overview", label: "Visao geral" },
  { id: "sellers", label: "Sellers" },
  { id: "products", label: "Produtos" },
  { id: "categories", label: "Categorias" },
  { id: "channels", label: "Canais e redes" },
  { id: "readiness", label: "Prontidao integracao" },
  { id: "commissions", label: "Comissoes" },
  { id: "settlements", label: "Repasses" },
  { id: "payouts", label: "Contas PIX" },
  { id: "contacts", label: "Contatos" },
  { id: "reviews", label: "Avaliacoes" },
  { id: "kyc", label: "KYC" },
  { id: "disputes", label: "Disputas" },
];

function parseError(payload, fallback = "Falha na API marketplace-admin.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  return fallback;
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao (${endpoint}). Verifique proxy ${BASE} (porta 8019).`;
  }
  return raw;
}

function formatBrl(cents) {
  const n = Number(cents);
  if (!Number.isFinite(n)) return "—";
  return `R$ ${(n / 100).toFixed(2)}`;
}

export default function OpsMarketplaceAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get("tab") || "overview";
  const [tab, setTab] = useState(TAB_ITEMS.some((t) => t.id === initialTab) ? initialTab : "overview");
  const [dashboard, setDashboard] = useState(null);
  const [sellers, setSellers] = useState([]);
  const [products, setProducts] = useState([]);
  const [commissions, setCommissions] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [categories, setCategories] = useState([]);
  const [categoryLinks, setCategoryLinks] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [payoutAccounts, setPayoutAccounts] = useState([]);
  const [settlementBatches, setSettlementBatches] = useState([]);
  const [kycDocs, setKycDocs] = useState([]);
  const [disputes, setDisputes] = useState([]);
  const [channelPartners, setChannelPartners] = useState([]);
  const [channelListings, setChannelListings] = useState([]);
  const [lockerNetworkLinks, setLockerNetworkLinks] = useState([]);
  const [channelParentGroup, setChannelParentGroup] = useState("");
  const [readinessRows, setReadinessRows] = useState([]);
  const [integrationIncidents, setIntegrationIncidents] = useState([]);
  const [integrationHub, setIntegrationHub] = useState(null);
  const [sellerForm, setSellerForm] = useState({
    legal_name: "",
    trade_name: "",
    tax_id: "",
    email: "",
    commission_pct: "5.00",
  });
  const [productForm, setProductForm] = useState({
    locker_id: "",
    product_id: "",
    price_cents: "",
    quantity: "1",
  });
  const [selectedId, setSelectedId] = useState("");
  const [selectedCommissionId, setSelectedCommissionId] = useState("");
  const [selectedBatchId, setSelectedBatchId] = useState("");
  const [categoryForm, setCategoryForm] = useState({ code: "", name: "" });
  const [categoryLinkCategoryId, setCategoryLinkCategoryId] = useState("");
  const [contactForm, setContactForm] = useState({ name: "", email: "", contact_type: "PRIMARY" });
  const [payoutForm, setPayoutForm] = useState({ pix_key: "", holder_name: "", account_type: "PIX" });
  const [kycForm, setKycForm] = useState({ doc_type: "CNPJ_CARD", file_ref: "" });
  const [disputeForm, setDisputeForm] = useState({ commission_id: "", reason: "" });
  const [listingChannelId, setListingChannelId] = useState("");
  const [listingStoreId, setListingStoreId] = useState("");
  const [networkChannelId, setNetworkChannelId] = useState("");
  const [networkLockerId, setNetworkLockerId] = useState("");
  const [selectedKycId, setSelectedKycId] = useState("");
  const [selectedDisputeId, setSelectedDisputeId] = useState("");
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

  const selectedSeller = sellers.find((s) => s.id === selectedId);

  const channelName = useCallback(
    (id) => channelPartners.find((p) => p.id === id)?.name || id,
    [channelPartners],
  );

  const filteredChannelPartners = useMemo(() => {
    if (!channelParentGroup) return channelPartners;
    return channelPartners.filter((p) => p.parent_group === channelParentGroup);
  }, [channelPartners, channelParentGroup]);

  const channelParentGroups = useMemo(() => {
    const groups = new Set(channelPartners.map((p) => p.parent_group).filter(Boolean));
    return [...groups].sort();
  }, [channelPartners]);

  const setTabAndUrl = (next) => {
    setTab(next);
    setSearchParams({ tab: next }, { replace: true });
  };

  useEffect(() => {
    const q = searchParams.get("tab");
    if (q && TAB_ITEMS.some((t) => t.id === q) && q !== tab) setTab(q);
  }, [searchParams, tab]);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErr("");
    setOk("");
    try {
      const sellerQ = selectedId ? `?seller_id=${encodeURIComponent(selectedId)}` : "";
      const [dash, s, p, c, r, cats, links, cont, pay, batches, kyc, disp, chp, chl, lnk, rd, inc, hub] = await Promise.all([
        fetch(`${API}/dashboard`, { headers }),
        fetch(`${API}/sellers`, { headers }),
        fetch(`${API}/seller-products${sellerQ}`, { headers }),
        fetch(`${API}/commissions${sellerQ}`, { headers }),
        fetch(`${API}/seller-reviews${sellerQ}`, { headers }),
        fetch(`${API}/categories`, { headers }),
        fetch(`${API}/seller-category-links${sellerQ}`, { headers }),
        fetch(`${API}/seller-contacts${sellerQ}`, { headers }),
        fetch(`${API}/seller-payout-accounts${sellerQ}`, { headers }),
        fetch(`${API}/seller-settlement-batches${sellerQ}`, { headers }),
        fetch(`${API}/seller-kyc-documents${sellerQ}`, { headers }),
        fetch(`${API}/seller-commission-disputes${sellerQ}`, { headers }),
        fetch(
          `${API}/channel-partners${channelParentGroup ? `?parent_group=${encodeURIComponent(channelParentGroup)}` : ""}`,
          { headers },
        ),
        fetch(`${API}/seller-channel-listings${sellerQ}`, { headers }),
        fetch(`${API}/seller-locker-network-links${sellerQ}`, { headers }),
        fetch(`${API}/integration-readiness?limit=120`, { headers }),
        fetch(`${API}/integration-incidents`, { headers }),
        fetch(`${API}/integration-hub/summary`, { headers }),
      ]);
      const dashJ = await dash.json().catch(() => ({}));
      const sj = await s.json().catch(() => ({}));
      const pj = await p.json().catch(() => ({}));
      const cj = await c.json().catch(() => ({}));
      const rj = await r.json().catch(() => ({}));
      if (!s.ok) throw new Error(parseError(sj));
      if (dash.ok) setDashboard(dashJ);
      const sellerList = sj.sellers || [];
      setSellers(sellerList);
      setProducts(pj.products || []);
      setCommissions(cj.commissions || []);
      setReviews(rj.reviews || []);
      setCategories((await cats.json().catch(() => ({}))).categories || []);
      setCategoryLinks((await links.json().catch(() => ({}))).links || []);
      setContacts((await cont.json().catch(() => ({}))).contacts || []);
      setPayoutAccounts((await pay.json().catch(() => ({}))).accounts || []);
      const batchList = (await batches.json().catch(() => ({}))).batches || [];
      setSettlementBatches(batchList);
      const kycJ = await kyc.json().catch(() => ({}));
      const dispJ = await disp.json().catch(() => ({}));
      const kycList = kycJ.documents || [];
      const dispList = dispJ.disputes || [];
      setKycDocs(kycList);
      setDisputes(dispList);
      setChannelPartners((await chp.json().catch(() => ({}))).partners || []);
      setChannelListings((await chl.json().catch(() => ({}))).listings || []);
      setLockerNetworkLinks((await lnk.json().catch(() => ({}))).links || []);
      setReadinessRows((await rd.json().catch(() => ({}))).items || []);
      setIntegrationIncidents((await inc.json().catch(() => ({}))).items || []);
      if (hub.ok) setIntegrationHub(await hub.json().catch(() => null));
      setSelectedId((prev) => prev || sellerList[0]?.id || "");
      const pending = (cj.commissions || []).filter((x) => x.status === "PENDING");
      setSelectedCommissionId((prev) => prev || pending[0]?.id || "");
      setSelectedBatchId((prev) => prev || batchList[0]?.id || "");
      setSelectedKycId((prev) => prev || kycList.filter((d) => d.status === "PENDING")[0]?.id || "");
      setSelectedDisputeId((prev) => prev || dispList.filter((d) => d.status === "OPEN")[0]?.id || "");
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
      setDashboard(null);
      setSellers([]);
      setProducts([]);
      setCommissions([]);
      setReviews([]);
      setCategories([]);
      setCategoryLinks([]);
      setContacts([]);
      setPayoutAccounts([]);
      setSettlementBatches([]);
      setKycDocs([]);
      setDisputes([]);
      setChannelPartners([]);
      setChannelListings([]);
      setLockerNetworkLinks([]);
    } finally {
      setLoading(false);
    }
  }, [token, headers, selectedId, channelParentGroup]);

  const onSeed = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seed`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Seed aplicado (sellers demo, produto, comissao e avaliacao).");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seed`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateSeller = async () => {
    if (!token || !canMutate || !sellerForm.legal_name || !sellerForm.tax_id || !sellerForm.email) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/sellers`, {
        method: "POST",
        headers,
        body: JSON.stringify(sellerForm),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Seller ${j.legal_name} criado.`);
      setSelectedId(j.id);
      setSellerForm({ legal_name: "", trade_name: "", tax_id: "", email: "", commission_pct: "5.00" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/sellers`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateProduct = async () => {
    if (!token || !canMutate || !selectedId || !productForm.locker_id || !productForm.product_id) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seller-products`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          seller_id: selectedId,
          locker_id: productForm.locker_id,
          product_id: productForm.product_id,
          price_cents: Number(productForm.price_cents) || 0,
          quantity: Number(productForm.quantity) || 0,
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Produto ${j.product_id} criado no locker ${j.locker_id}.`);
      setProductForm({ locker_id: "", product_id: "", price_cents: "", quantity: "1" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seller-products`));
    } finally {
      setLoading(false);
    }
  };

  const onApproveSeller = async () => {
    if (!token || !canMutate || !selectedId || selectedSeller?.status !== "PENDING_APPROVAL") return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/sellers/${encodeURIComponent(selectedId)}`, {
        method: "PATCH",
        headers,
        body: JSON.stringify({ status: "ACTIVE" }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Seller ${selectedId} aprovado (ACTIVE).`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/sellers/...`));
    } finally {
      setLoading(false);
    }
  };

  const onWebhook = async () => {
    if (!token || !canMutate || !selectedId || !webhookUrl) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/sellers/${encodeURIComponent(selectedId)}/webhook`, {
        method: "PUT",
        headers,
        body: JSON.stringify({
          url: webhookUrl,
          secret: webhookSecret || undefined,
          events: ["order.created", "commission.settled"],
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Webhook salvo para seller ${selectedId}.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/sellers/.../webhook`));
    } finally {
      setLoading(false);
    }
  };

  const onRotateKey = async () => {
    if (!token || !canMutate || !selectedId) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/sellers/${encodeURIComponent(selectedId)}/api-keys/rotate`, {
        method: "POST",
        headers,
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setLastApiKey(j.api_key || "");
      setOk(`Nova API key (${j.key_prefix}…). Copie agora.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/sellers/.../api-keys/rotate`));
    } finally {
      setLoading(false);
    }
  };

  const onSettleCommission = async () => {
    if (!token || !canMutate || !selectedCommissionId) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/commissions/${encodeURIComponent(selectedCommissionId)}`, {
        method: "PATCH",
        headers,
        body: JSON.stringify({ status: "SETTLED" }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Comissao ${selectedCommissionId} liquidada (SETTLED).`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/commissions/...`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateCategory = async () => {
    if (!token || !canMutate || !categoryForm.code || !categoryForm.name) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/categories`, { method: "POST", headers, body: JSON.stringify(categoryForm) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Categoria ${j.code} criada.`);
      setCategoryForm({ code: "", name: "" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/categories`));
    } finally {
      setLoading(false);
    }
  };

  const onLinkCategory = async () => {
    if (!token || !canMutate || !selectedId || !categoryLinkCategoryId) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seller-category-links`, {
        method: "POST",
        headers,
        body: JSON.stringify({ seller_id: selectedId, category_id: categoryLinkCategoryId, is_primary: false }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Categoria vinculada ao seller.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seller-category-links`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateContact = async () => {
    if (!token || !canMutate || !selectedId || !contactForm.name) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seller-contacts`, {
        method: "POST",
        headers,
        body: JSON.stringify({ seller_id: selectedId, ...contactForm }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Contato ${j.name} criado.`);
      setContactForm({ name: "", email: "", contact_type: "PRIMARY" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seller-contacts`));
    } finally {
      setLoading(false);
    }
  };

  const onCreatePayout = async () => {
    if (!token || !canMutate || !selectedId || !payoutForm.holder_name) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seller-payout-accounts`, {
        method: "POST",
        headers,
        body: JSON.stringify({ seller_id: selectedId, is_default: true, ...payoutForm }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Conta de repasse criada.");
      setPayoutForm({ pix_key: "", holder_name: "", account_type: "PIX" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seller-payout-accounts`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateSettlement = async () => {
    if (!token || !canMutate || !selectedId) return;
    const today = new Date().toISOString().slice(0, 10);
    const start = today.slice(0, 8) + "01";
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seller-settlement-batches`, {
        method: "POST",
        headers,
        body: JSON.stringify({ seller_id: selectedId, period_start: start, period_end: today, fees_cents: 0 }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Lote de repasse ${j.id} criado (${j.commission_count} comissoes).`);
      setSelectedBatchId(j.id);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seller-settlement-batches`));
    } finally {
      setLoading(false);
    }
  };

  const onMarkBatchPaid = async () => {
    if (!token || !canMutate || !selectedBatchId) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seller-settlement-batches/${encodeURIComponent(selectedBatchId)}`, {
        method: "PATCH",
        headers,
        body: JSON.stringify({ status: "PAID", settlement_ref: `PIX-${Date.now()}` }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Lote ${selectedBatchId} marcado como PAID.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seller-settlement-batches/...`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateKyc = async () => {
    if (!token || !canMutate || !selectedId || !kycForm.doc_type) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seller-kyc-documents`, {
        method: "POST",
        headers,
        body: JSON.stringify({ seller_id: selectedId, ...kycForm }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Documento KYC ${j.doc_type} registrado.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seller-kyc-documents`));
    } finally {
      setLoading(false);
    }
  };

  const onApproveKyc = async () => {
    if (!token || !canMutate || !selectedKycId) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seller-kyc-documents/${encodeURIComponent(selectedKycId)}`, {
        method: "PATCH",
        headers,
        body: JSON.stringify({ status: "APPROVED" }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`KYC ${selectedKycId} aprovado.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seller-kyc-documents/...`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateDispute = async () => {
    if (!token || !canMutate || !selectedId || !disputeForm.commission_id || !disputeForm.reason) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seller-commission-disputes`, {
        method: "POST",
        headers,
        body: JSON.stringify({ seller_id: selectedId, ...disputeForm }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Disputa aberta (${j.id}).`);
      setDisputeForm({ commission_id: "", reason: "" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seller-commission-disputes`));
    } finally {
      setLoading(false);
    }
  };

  const onSeedChannelPlayers = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/channel-partners/seed-players`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(
        `Catalogo sincronizado: +${j.inserted ?? 0} novos, ${j.updated ?? 0} atualizados, ${j.capabilities ?? 0} capacidades novas.`,
      );
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/channel-partners/seed-players`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateChannelListing = async () => {
    if (!token || !canMutate || !selectedId || !listingChannelId) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seller-channel-listings`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          seller_id: selectedId,
          channel_partner_id: listingChannelId,
          external_store_id: listingStoreId || undefined,
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Listing de canal criado.");
      setListingStoreId("");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seller-channel-listings`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateLockerNetwork = async () => {
    if (!token || !canMutate || !selectedId || !networkChannelId) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seller-locker-network-links`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          seller_id: selectedId,
          channel_partner_id: networkChannelId,
          locker_id: networkLockerId || undefined,
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Rede de locker vinculada ao seller.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seller-locker-network-links`));
    } finally {
      setLoading(false);
    }
  };

  const onResolveDispute = async () => {
    if (!token || !canMutate || !selectedDisputeId) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seller-commission-disputes/${encodeURIComponent(selectedDisputeId)}`, {
        method: "PATCH",
        headers,
        body: JSON.stringify({ status: "RESOLVED", resolution_notes: "Resolvido via OPS" }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Disputa ${selectedDisputeId} resolvida.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seller-commission-disputes/...`));
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = selectedId ? products.filter((p) => p.seller_id === selectedId) : products;
  const filteredCommissions = selectedId ? commissions.filter((c) => c.seller_id === selectedId) : commissions;
  const filteredReviews = selectedId ? reviews.filter((r) => r.seller_id === selectedId) : reviews;

  const pendingCommissions = commissions.filter((c) => c.status === "PENDING");

  const tableRows =
    tab === "sellers"
      ? sellers.map((s) => ({
          key: `s-${s.id}`,
          tipo: "seller",
          id: s.tax_id || s.id,
          detalhe: `${s.trade_name || s.legal_name} · ${s.status} · comissao ${s.commission_pct}% · pedidos ${s.total_orders ?? 0}`,
        }))
      : tab === "products"
        ? filteredProducts.map((p) => ({
            key: `p-${p.id}`,
            tipo: "product",
            id: p.product_id,
            detalhe: `${p.locker_id} · ${formatBrl(p.price_cents)} · qtd ${p.quantity} · ${p.status}`,
          }))
        : tab === "readiness"
          ? [
              ...readinessRows.map((row) => ({
                key: `rd-${row.channel_partner_id}`,
                tipo: row.readiness_band,
                id: row.partner_code,
                detalhe: `score ${row.score_total} · caps ${row.score_capabilities} · api ${row.score_api} · ops ${row.score_operations} · blockers ${(row.blockers || []).length}`,
              })),
              ...integrationIncidents.map((i) => ({
                key: `inc-${i.id}`,
                tipo: i.severity,
                id: i.partner_code,
                detalhe: `${i.incident_type} · ${i.title} · ${i.status}`,
              })),
            ]
          : tab === "channels"
          ? [
              ...filteredChannelPartners.map((p) => ({
                key: `chp-${p.id}`,
                tipo: p.partner_role,
                id: p.code,
                detalhe: `${p.name} · ${p.parent_group || "—"} · ${p.integration_mode || "—"} · ${p.country} · caps ${(p.capabilities || []).length} · lockers:${p.supports_lockers ? "Y" : "N"} · ref ${p.locker_operator_ref || "—"}`,
              })),
              ...channelListings.map((l) => ({
                key: `chl-${l.id}`,
                tipo: "listing",
                id: l.external_store_id || l.id.slice(0, 12),
                detalhe: `seller ${l.seller_id.slice(0, 8)} · ${channelName(l.channel_partner_id)} · ${l.listing_status}`,
              })),
              ...lockerNetworkLinks.map((n) => ({
                key: `lnk-${n.id}`,
                tipo: "locker_network",
                id: n.locker_id || "rede",
                detalhe: `${channelName(n.channel_partner_id)} · prio ${n.priority} · seller ${n.seller_id.slice(0, 8)}`,
              })),
            ]
          : tab === "categories"
          ? [
              ...categories.map((cat) => ({
                key: `cat-${cat.id}`,
                tipo: "category",
                id: cat.code,
                detalhe: `${cat.name} · ${cat.active ? "ativa" : "inativa"}`,
              })),
              ...categoryLinks.map((l) => ({
                key: `link-${l.id}`,
                tipo: "seller_category",
                id: l.category_id,
                detalhe: `seller ${l.seller_id} · ${l.is_primary ? "principal" : "secundaria"}`,
              })),
            ]
          : tab === "commissions"
            ? filteredCommissions.map((c) => ({
                key: `c-${c.id}`,
                tipo: "commission",
                id: c.order_id,
                detalhe: `${formatBrl(c.commission_amount_cents)} comissao · liquido ${formatBrl(c.net_to_seller_cents)} · ${c.status}`,
              }))
            : tab === "settlements"
              ? settlementBatches.map((b) => ({
                  key: `b-${b.id}`,
                  tipo: "settlement_batch",
                  id: b.id.slice(0, 12),
                  detalhe: `${b.period_start} a ${b.period_end} · ${formatBrl(b.net_payout_cents)} · ${b.status} · ${b.commission_count} itens`,
                }))
              : tab === "payouts"
                ? payoutAccounts.map((a) => ({
                    key: `pay-${a.id}`,
                    tipo: a.account_type,
                    id: a.pix_key || a.account_number || a.id.slice(0, 8),
                    detalhe: `${a.holder_name} · ${a.verified ? "verificada" : "pendente"} · ${a.is_default ? "default" : ""}`,
                  }))
                : tab === "contacts"
                  ? contacts.map((c) => ({
                      key: `ct-${c.id}`,
                      tipo: c.contact_type,
                      id: c.name,
                      detalhe: `${c.email || "—"} · ${c.phone || "—"} · ${c.is_primary ? "principal" : ""}`,
                    }))
                  : tab === "kyc"
                    ? kycDocs.map((d) => ({
                        key: `kyc-${d.id}`,
                        tipo: d.doc_type,
                        id: d.id.slice(0, 12),
                        detalhe: `${d.status} · ${d.file_ref || "sem arquivo"}`,
                      }))
                    : tab === "disputes"
                      ? disputes.map((d) => ({
                          key: `disp-${d.id}`,
                          tipo: "dispute",
                          id: d.commission_id.slice(0, 12),
                          detalhe: `${d.status} · ${(d.reason || "").slice(0, 60)}`,
                        }))
                      : filteredReviews.map((r) => ({
                          key: `r-${r.id}`,
                          tipo: "review",
                          id: r.order_id,
                          detalhe: `nota ${r.rating}/5 · ${(r.comment || "").slice(0, 80) || "sem comentario"}`,
                        }));

  const listCount = tableRows.length;

  const listTitle =
    tab === "overview"
      ? "Indicadores (dashboard)"
      : tab === "sellers"
        ? `Sellers (${sellers.length})`
        : tab === "products"
          ? `Produtos por locker (${filteredProducts.length})`
          : tab === "channels"
            ? `Players (${filteredChannelPartners.length}/${channelPartners.length}) · listings (${channelListings.length}) · redes locker (${lockerNetworkLinks.length})`
            : tab === "categories"
            ? `Categorias (${categories.length}) e vinculos (${categoryLinks.length})`
            : tab === "commissions"
              ? `Comissoes (${filteredCommissions.length})`
              : tab === "settlements"
                ? `Lotes de repasse (${settlementBatches.length})`
                : tab === "payouts"
                  ? `Contas de repasse (${payoutAccounts.length})`
                  : tab === "contacts"
                    ? `Contatos (${contacts.length})`
                    : tab === "kyc"
                      ? `Documentos KYC (${kycDocs.length})`
                      : tab === "disputes"
                        ? `Disputas (${disputes.length})`
                        : `Avaliacoes (${filteredReviews.length})`;

  return (
    <div style={pageStyle} data-testid="ops-marketplace-admin-page">
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
          <Link to="/ops/order-pickup/admin" style={crossShortcutLinkStyle}>
            Order Pickup
          </Link>
          <Link to="/ops/access/user-roles" style={crossShortcutLinkStyle}>
            user_roles
          </Link>
        </div>

        <OpsPageTitleHeader
          title="OPS — Marketplace (admin)"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Sellers, canais (InPost, DHL, Magalu, ML, Amazon, Correios, CTT, DPD), redes locker, repasses e KYC —{" "}
          <code style={{ color: "#e2e8f0" }}>{API}</code> — role{" "}
          <code style={{ color: "#e2e8f0" }}>admin_operacao</code> para escrita.
        </p>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Seller em foco</h3>
          </div>
          <div style={healthLocalFilterRowStyle}>
            <label style={healthLocalFilterFieldStyle}>
              seller_id
              <select
                value={selectedId}
                onChange={(e) => setSelectedId(e.target.value)}
                style={healthLocalFilterInputStyle}
              >
                <option value="">— selecione —</option>
                {sellers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.trade_name || s.legal_name} — {s.status}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {selectedSeller ? (
            <p style={summary24hHintStyle}>
              {selectedSeller.legal_name} · CNPJ {selectedSeller.tax_id} · rating {selectedSeller.seller_rating ?? "—"}
            </p>
          ) : null}
        </section>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Area de cadastro</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {TAB_ITEMS.map((t) => (
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

          {tab === "sellers" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                legal_name
                <input
                  value={sellerForm.legal_name}
                  onChange={(e) => setSellerForm((f) => ({ ...f, legal_name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="Razao social"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                trade_name
                <input
                  value={sellerForm.trade_name}
                  onChange={(e) => setSellerForm((f) => ({ ...f, trade_name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                tax_id
                <input
                  value={sellerForm.tax_id}
                  onChange={(e) => setSellerForm((f) => ({ ...f, tax_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="CNPJ"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                email
                <input
                  value={sellerForm.email}
                  onChange={(e) => setSellerForm((f) => ({ ...f, email: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                commission_pct
                <input
                  value={sellerForm.commission_pct}
                  onChange={(e) => setSellerForm((f) => ({ ...f, commission_pct: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
            </div>
          ) : null}

          {tab === "products" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                locker_id
                <input
                  value={productForm.locker_id}
                  onChange={(e) => setProductForm((f) => ({ ...f, locker_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="LOCKER-DEMO-01"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                product_id
                <input
                  value={productForm.product_id}
                  onChange={(e) => setProductForm((f) => ({ ...f, product_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                price_cents
                <input
                  value={productForm.price_cents}
                  onChange={(e) => setProductForm((f) => ({ ...f, price_cents: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="4990"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                quantity
                <input
                  value={productForm.quantity}
                  onChange={(e) => setProductForm((f) => ({ ...f, quantity: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
            </div>
          ) : null}

          {tab === "categories" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                code
                <input
                  value={categoryForm.code}
                  onChange={(e) => setCategoryForm((f) => ({ ...f, code: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                name
                <input
                  value={categoryForm.name}
                  onChange={(e) => setCategoryForm((f) => ({ ...f, name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                category_id (vinculo)
                <select
                  value={categoryLinkCategoryId}
                  onChange={(e) => setCategoryLinkCategoryId(e.target.value)}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="">— selecione —</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.code}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ) : null}

          {tab === "contacts" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                name
                <input
                  value={contactForm.name}
                  onChange={(e) => setContactForm((f) => ({ ...f, name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                email
                <input
                  value={contactForm.email}
                  onChange={(e) => setContactForm((f) => ({ ...f, email: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                contact_type
                <select
                  value={contactForm.contact_type}
                  onChange={(e) => setContactForm((f) => ({ ...f, contact_type: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="PRIMARY">PRIMARY</option>
                  <option value="SUPPORT">SUPPORT</option>
                  <option value="FINANCE">FINANCE</option>
                </select>
              </label>
            </div>
          ) : null}

          {tab === "payouts" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                holder_name
                <input
                  value={payoutForm.holder_name}
                  onChange={(e) => setPayoutForm((f) => ({ ...f, holder_name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                pix_key
                <input
                  value={payoutForm.pix_key}
                  onChange={(e) => setPayoutForm((f) => ({ ...f, pix_key: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
            </div>
          ) : null}

          {tab === "kyc" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                doc_type
                <select
                  value={kycForm.doc_type}
                  onChange={(e) => setKycForm((f) => ({ ...f, doc_type: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="CNPJ_CARD">CNPJ_CARD</option>
                  <option value="ID">ID</option>
                  <option value="ADDRESS">ADDRESS</option>
                  <option value="BANK_PROOF">BANK_PROOF</option>
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                file_ref
                <input
                  value={kycForm.file_ref}
                  onChange={(e) => setKycForm((f) => ({ ...f, file_ref: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                kyc_id (aprovar)
                <select value={selectedKycId} onChange={(e) => setSelectedKycId(e.target.value)} style={healthLocalFilterInputStyle}>
                  <option value="">— selecione —</option>
                  {kycDocs.filter((d) => d.status === "PENDING").map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.doc_type} · {d.seller_id.slice(0, 8)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ) : null}

          {tab === "disputes" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                commission_id
                <input
                  value={disputeForm.commission_id}
                  onChange={(e) => setDisputeForm((f) => ({ ...f, commission_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                reason
                <input
                  value={disputeForm.reason}
                  onChange={(e) => setDisputeForm((f) => ({ ...f, reason: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                dispute_id (resolver)
                <select
                  value={selectedDisputeId}
                  onChange={(e) => setSelectedDisputeId(e.target.value)}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="">— selecione —</option>
                  {disputes.filter((d) => d.status === "OPEN").map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.commission_id.slice(0, 12)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ) : null}

          {tab === "commissions" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                commission_id (PENDING)
                <select
                  value={selectedCommissionId}
                  onChange={(e) => setSelectedCommissionId(e.target.value)}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="">— selecione —</option>
                  {pendingCommissions.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.order_id} · {formatBrl(c.commission_amount_cents)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ) : null}

          {tab === "settlements" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                batch_id
                <select value={selectedBatchId} onChange={(e) => setSelectedBatchId(e.target.value)} style={healthLocalFilterInputStyle}>
                  <option value="">— selecione —</option>
                  {settlementBatches.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.id.slice(0, 12)} · {b.status} · {formatBrl(b.net_payout_cents)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ) : null}

          {tab === "overview" ? (
            <p style={summary24hHintStyle}>
              KPIs do marketplace. Aba Canais: ~47 players (locker, marketplace, carrier, agregador, pagamentos) com modo de integracao e capacidades (webhook, OAuth, label API).
            </p>
          ) : null}

          {tab === "channels" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                parent_group
                <select
                  value={channelParentGroup}
                  onChange={(e) => setChannelParentGroup(e.target.value)}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="">— todos —</option>
                  {channelParentGroups.map((g) => (
                    <option key={g} value={g}>
                      {g}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ) : null}

          {tab === "channels" && channelPartners.length === 0 ? (
            <p style={summary24hHintStyle}>
              Nenhum player cadastrado. Use Seed ou Sync catalogo (~47 players: InPost, Mondial Relay, Melhor Envio, TikTok, Stripe Connect, etc.).
            </p>
          ) : null}

          {tab === "products" && !selectedId ? (
            <p style={summary24hHintStyle}>Selecione um seller em foco para criar produto no locker.</p>
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
                <button type="button" style={buttonGhostStyle} onClick={() => void onSeedChannelPlayers()} disabled={loading}>
                  Sync catalogo players
                </button>
                {tab === "sellers" ? (
                  <>
                    <button
                      type="button"
                      style={buttonPrimaryStyle}
                      onClick={() => void onCreateSeller()}
                      disabled={loading || !sellerForm.legal_name || !sellerForm.tax_id || !sellerForm.email}
                    >
                      Criar seller
                    </button>
                    <button
                      type="button"
                      style={buttonGhostStyle}
                      onClick={() => void onApproveSeller()}
                      disabled={loading || !selectedId || selectedSeller?.status !== "PENDING_APPROVAL"}
                    >
                      Aprovar seller
                    </button>
                  </>
                ) : null}
                {tab === "products" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreateProduct()}
                    disabled={
                      loading || !selectedId || !productForm.locker_id || !productForm.product_id || !productForm.price_cents
                    }
                  >
                    Criar produto
                  </button>
                ) : null}
                {tab === "channels" ? (
                  <>
                    <button
                      type="button"
                      style={buttonPrimaryStyle}
                      onClick={() => void onCreateChannelListing()}
                      disabled={loading || !selectedId || !listingChannelId}
                    >
                      Vincular canal (listing)
                    </button>
                    <button
                      type="button"
                      style={buttonGhostStyle}
                      onClick={() => void onCreateLockerNetwork()}
                      disabled={loading || !selectedId || !networkChannelId}
                    >
                      Vincular rede locker
                    </button>
                  </>
                ) : null}
                {tab === "categories" ? (
                  <>
                    <button
                      type="button"
                      style={buttonPrimaryStyle}
                      onClick={() => void onCreateCategory()}
                      disabled={loading || !categoryForm.code || !categoryForm.name}
                    >
                      Criar categoria
                    </button>
                    <button
                      type="button"
                      style={buttonGhostStyle}
                      onClick={() => void onLinkCategory()}
                      disabled={loading || !selectedId || !categoryLinkCategoryId}
                    >
                      Vincular ao seller
                    </button>
                  </>
                ) : null}
                {tab === "contacts" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreateContact()}
                    disabled={loading || !selectedId || !contactForm.name}
                  >
                    Criar contato
                  </button>
                ) : null}
                {tab === "payouts" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreatePayout()}
                    disabled={loading || !selectedId || !payoutForm.holder_name}
                  >
                    Criar conta PIX
                  </button>
                ) : null}
                {tab === "settlements" ? (
                  <>
                    <button
                      type="button"
                      style={buttonPrimaryStyle}
                      onClick={() => void onCreateSettlement()}
                      disabled={loading || !selectedId}
                    >
                      Gerar lote de repasse
                    </button>
                    <button
                      type="button"
                      style={buttonGhostStyle}
                      onClick={() => void onMarkBatchPaid()}
                      disabled={loading || !selectedBatchId}
                    >
                      Marcar lote PAID
                    </button>
                  </>
                ) : null}
                {tab === "kyc" ? (
                  <>
                    <button
                      type="button"
                      style={buttonPrimaryStyle}
                      onClick={() => void onCreateKyc()}
                      disabled={loading || !selectedId}
                    >
                      Registrar documento
                    </button>
                    <button
                      type="button"
                      style={buttonGhostStyle}
                      onClick={() => void onApproveKyc()}
                      disabled={loading || !selectedKycId}
                    >
                      Aprovar KYC
                    </button>
                  </>
                ) : null}
                {tab === "disputes" ? (
                  <>
                    <button
                      type="button"
                      style={buttonPrimaryStyle}
                      onClick={() => void onCreateDispute()}
                      disabled={loading || !selectedId || !disputeForm.commission_id || !disputeForm.reason}
                    >
                      Abrir disputa
                    </button>
                    <button
                      type="button"
                      style={buttonGhostStyle}
                      onClick={() => void onResolveDispute()}
                      disabled={loading || !selectedDisputeId}
                    >
                      Resolver disputa
                    </button>
                  </>
                ) : null}
                {tab === "commissions" ? (
                  <button
                    type="button"
                    style={buttonGhostStyle}
                    onClick={() => void onSettleCommission()}
                    disabled={loading || !selectedCommissionId}
                  >
                    Liquidar comissao
                  </button>
                ) : null}
              </>
            ) : null}
          </div>
        </section>

        {tab !== "overview" ? (
        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Webhook e API key (seller)</h3>
          </div>
          <div style={healthLocalFilterRowStyle}>
            <label style={healthLocalFilterFieldStyle}>
              seller_id
              <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} style={healthLocalFilterInputStyle}>
                <option value="">— selecione —</option>
                {sellers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.trade_name || s.legal_name}
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
            <button type="button" style={buttonGhostStyle} onClick={() => void onRotateKey()} disabled={!canMutate || !selectedId}>
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

        {tab === "overview" && dashboard ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>{listTitle}</h3>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12 }}>
              {[
                ["Sellers ativos", dashboard.sellers_active],
                ["Pendentes aprovacao", dashboard.sellers_pending_approval],
                ["Produtos ativos", dashboard.products_active],
                ["Comissoes pendentes", dashboard.commissions_pending],
                ["Valor pendente", formatBrl(dashboard.commissions_pending_cents)],
                ["Comissoes liquidadas", dashboard.commissions_settled],
                ["Disputas abertas", dashboard.open_disputes],
                ["Lotes repasse (draft)", dashboard.settlement_batches_draft],
                ["KYC pendente", dashboard.kyc_pending],
                ["Rating medio", dashboard.avg_seller_rating ?? "—"],
                ["Players ativos", dashboard.channel_partners_active],
                ["GO_LIVE (prontidao)", dashboard.integration_go_live],
                ["Score medio integracao", dashboard.integration_avg_score],
                ["Incidentes abertos", dashboard.integration_open_incidents],
                ["Listings canal", dashboard.seller_channel_listings],
                ["Redes locker", dashboard.locker_network_links],
              ].map(([label, value]) => (
                <div key={label} style={{ padding: 10, borderRadius: 8, border: "1px solid rgba(148,163,184,0.25)" }}>
                  <p style={{ margin: 0, fontSize: 11, opacity: 0.75 }}>{label}</p>
                  <p style={{ margin: "4px 0 0", fontSize: 18, fontWeight: 600 }}>{value}</p>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {tab !== "overview" && listCount > 0 ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>{listTitle}</h3>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["tipo", "id", "detalhe"].map((h) => (
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
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : tab !== "overview" && token && !loading ? (
          <p style={summary24hHintStyle}>Nenhum registro. Use Listar ou Seed (admin_operacao).</p>
        ) : tab === "overview" && token && !dashboard && !loading ? (
          <p style={summary24hHintStyle}>Clique em Listar para carregar o dashboard.</p>
        ) : null}
      </section>
    </div>
  );
}

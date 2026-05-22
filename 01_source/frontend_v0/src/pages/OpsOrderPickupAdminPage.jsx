
import React, { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
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
const PAGE_VERSION = "ops/order-pickup/admin v0.1";

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
  const [tab, setTab] = useState("partners");
  const [partnerSubTab, setPartnerSubTab] = useState("ecommerce");
  const [ecItems, setEcItems] = useState([]);
  const [lgItems, setLgItems] = useState([]);
  const [orders, setOrders] = useState([]);
  const [pickups, setPickups] = useState([]);
  const [outbox, setOutbox] = useState([]);
  const [fulfillment, setFulfillment] = useState([]);
  const [partnerForm, setPartnerForm] = useState({ name: "", code: "" });
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
      const [ec, lg, ord, pk, ob, ft] = await Promise.all([
        fetch(`${API}/ecommerce-partners`, { headers }),
        fetch(`${API}/logistics-partners`, { headers }),
        fetch(`${API}/orders`, { headers }),
        fetch(`${API}/pickups`, { headers }),
        fetch(`${API}/integration-outbox`, { headers }),
        fetch(`${API}/fulfillment-tracking`, { headers }),
      ]);
      const ecJson = await ec.json().catch(() => ({}));
      const lgJson = await lg.json().catch(() => ({}));
      const ordJson = await ord.json().catch(() => ({}));
      const pkJson = await pk.json().catch(() => ({}));
      const obJson = await ob.json().catch(() => ({}));
      const ftJson = await ft.json().catch(() => ({}));
      if (!ec.ok) throw new Error(parseError(ecJson));
      if (!lg.ok) throw new Error(parseError(lgJson));
      if (!ord.ok) throw new Error(parseError(ordJson));
      if (!pk.ok) throw new Error(parseError(pkJson));
      if (!ob.ok) throw new Error(parseError(obJson));
      if (!ft.ok) throw new Error(parseError(ftJson));
      setEcItems(ecJson.partners || []);
      setLgItems(lgJson.partners || []);
      setOrders(ordJson.items || []);
      setPickups(pkJson.items || []);
      setOutbox(obJson.items || []);
      setFulfillment(ftJson.items || []);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
      setEcItems([]);
      setLgItems([]);
      setOrders([]);
      setPickups([]);
      setOutbox([]);
      setFulfillment([]);
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

  const tableRows =
    tab === "partners"
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
        ? orders.map((o) => ({
            key: `ord-${o.id}`,
            tipo: "order",
            id: o.id,
            detalhe: `${o.status} / ${o.payment_status} · R$ ${formatMoney(o.amount_cents)} · partner ${o.ecommerce_partner_id || "—"} · pickups ${pickups.filter((p) => p.order_id === o.id).length}`,
          }))
        : [
            ...outbox.map((x) => ({
              key: `ob-${x.id}`,
              tipo: "outbox",
              id: x.id,
              detalhe: `${x.event_type} · ${x.status} · order ${x.order_id}`,
              replayId: x.id,
            })),
            ...fulfillment.map((x) => ({
              key: `ft-${x.id}`,
              tipo: "fulfillment",
              id: x.order_id,
              detalhe: `${x.fulfillment_type} · ${x.status} · ${x.last_event_type || "—"}`,
            })),
          ];

  const listCount = tableRows.length;

  const listTitle =
    tab === "partners"
      ? `Parceiros (e-commerce: ${ecItems.length}, logística: ${lgItems.length})`
      : tab === "orders"
        ? `Pedidos (${orders.length}) · pickups (${pickups.length})`
        : `Integração (outbox: ${outbox.length}, fulfillment: ${fulfillment.length})`;

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
          title="OPS — Order Pickup (admin)"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Parceiros pickup, pedidos, credits, outbox e fulfillment — <code style={{ color: "#e2e8f0" }}>{API}</code> — role{" "}
          <code style={{ color: "#e2e8f0" }}>admin_operacao</code> para escrita.
        </p>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Área de cadastro</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button type="button" style={tabButtonStyle(tab === "partners")} onClick={() => setTab("partners")}>
                Parceiros
              </button>
              <button type="button" style={tabButtonStyle(tab === "orders")} onClick={() => setTab("orders")}>
                Pedidos
              </button>
              <button type="button" style={tabButtonStyle(tab === "integration")} onClick={() => setTab("integration")}>
                Integração
              </button>
            </div>
          </div>

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

          {tab === "integration" ? (
            <p style={summary24hHintStyle}>
              Outbox de eventos para parceiros (replay manual) e rastreamento de fulfillment por pedido.
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
                              onClick={() => void onReplay(row.replayId)}
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

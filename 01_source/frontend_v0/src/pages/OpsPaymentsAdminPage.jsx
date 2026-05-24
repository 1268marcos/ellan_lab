
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import PaymentsEcosystemGraph from "../components/payments/PaymentsEcosystemGraph";
import PaymentsMilestoneCrud from "../components/payments/PaymentsMilestoneCrud";
import PaymentsRoutingCrud from "../components/payments/PaymentsRoutingCrud";
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

const BASE = import.meta.env.VITE_PAYMENTS_ADMIN_BASE_URL || "/api/pya";
const API = `${BASE}/v1/payments-admin`;
const PAGE_VERSION = "ops/payments/admin v0.2-cross-domain";

const TABS = [
  ["intelligence", "Inteligencia"],
  ["cross-domain", "Hub cross-domain"],
  ["graph", "Grafo"],
  ["ecosystem", "Ecossistema"],
  ["segments", "Segmentos"],
  ["integrations", "Integracoes"],
  ["coverage", "Cobertura pais"],
  ["milestones", "Roadmap"],
  ["corridors", "Corredores FX"],
  ["compliance", "Compliance"],
  ["routing", "Roteamento"],
  ["incidents", "Incidentes"],
  ["relations", "Relacoes"],
  ["order-context", "Contexto pedido"],
  ["transactions", "Transacoes"],
  ["instructions", "Instrucoes"],
  ["splits", "Splits"],
  ["payments", "Ledger"],
  ["batches", "Lotes conciliacao"],
  ["webhooks", "Webhooks"],
  ["deliveries", "Entregas WH"],
  ["holds", "Holds"],
  ["vault", "Cartoes salvos"],
  ["events", "Gateway events"],
];

function parseError(payload, fallback = "Falha na API payments-admin.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  return fallback;
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao (${endpoint}). Verifique proxy ${BASE} (porta 8126).`;
  }
  return raw;
}

export default function OpsPaymentsAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get("tab") || "intelligence";
  const [orderFilter, setOrderFilter] = useState("ORD-DEMO-INPOST-001");
  const [summary, setSummary] = useState(null);
  const [ecosystemGraph, setEcosystemGraph] = useState(null);
  const [orderGraph, setOrderGraph] = useState(null);
  const [rows, setRows] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [selectedWebhook, setSelectedWebhook] = useState("");
  const [lastSecret, setLastSecret] = useState("");
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

  const setTab = (next) => {
    const p = new URLSearchParams(searchParams);
    p.set("tab", next);
    setSearchParams(p, { replace: true });
  };

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErr("");
    setOk("");
    const qs = orderFilter.trim() ? `?order_id=${encodeURIComponent(orderFilter.trim())}` : "";
    try {
      if (tab === "cross-domain") {
        const [reg, gaps, obs, refs] = await Promise.all([
          fetch(`${API}/cross-domain/registry`, { headers }),
          fetch(`${API}/cross-domain/gaps`, { headers }),
          fetch(`${API}/cross-domain/obligations?status=PENDING`, { headers }),
          fetch(
            orderFilter.trim()
              ? `${API}/cross-domain/external-references?order_id=${encodeURIComponent(orderFilter.trim())}`
              : `${API}/cross-domain/external-references`,
            { headers },
          ),
        ]);
        const regJ = await reg.json();
        const gapsJ = await gaps.json();
        const obsJ = await obs.json();
        const refsJ = await refs.json();
        setRows([
          ...(refsJ.items || []).map((r) => ({ ...r, _kind: "ref" })),
          ...(obsJ.items || []).map((o) => ({ ...o, _kind: "obligation", id: o.id })),
          ...(gapsJ.items || []).map((g, i) => ({
            id: `gap-${i}`,
            _kind: "gap",
            order_id: g.order_id,
            code: g.domain_code,
            detalhe: g.message,
          })),
        ]);
        setSummary({
          registry_total: (regJ.items || []).length,
          gaps_total: gapsJ.total,
          obligations_pending: obsJ.total,
        });
        setEcosystemGraph(null);
        return;
      }

      if (tab === "intelligence" || tab === "graph") {
        if (tab === "intelligence") {
          const r = await fetch(`${API}/intelligence/summary`, { headers });
          const j = await r.json().catch(() => ({}));
          if (!r.ok) throw new Error(parseError(j));
          setSummary(j);
          if (orderFilter.trim()) {
            const g = await fetch(`${API}/intelligence/order-graph/${encodeURIComponent(orderFilter.trim())}`, {
              headers,
            });
            setOrderGraph(await g.json().catch(() => null));
          } else setOrderGraph(null);
        } else {
          setSummary(null);
          setOrderGraph(null);
        }
        const gr = await fetch(`${API}/intelligence/ecosystem-graph`, { headers });
        const gj = await gr.json().catch(() => ({}));
        if (!gr.ok) throw new Error(parseError(gj));
        setEcosystemGraph(gj);
        setRows([]);
        return;
      }
      setSummary(null);
      setEcosystemGraph(null);
      setOrderGraph(null);
      const paths = {
        ecosystem: `${API}/ecosystem-players`,
        segments: `${API}/ecosystem-segments`,
        integrations: `${API}/player-integrations`,
        coverage: `${API}/player-country-coverage`,
        milestones: `${API}/integration-milestones`,
        corridors: `${API}/settlement-corridors`,
        compliance: `${API}/player-compliance`,
        routing: `${API}/routing-rules?active_only=false`,
        incidents: `${API}/integration-incidents`,
        relations: `${API}/player-relations`,
        "order-context": `${API}/order-context`,
        transactions: `${API}/payment-transactions${qs}`,
        instructions: `${API}/payment-instructions${qs}`,
        splits: `${API}/payment-splits${qs}`,
        payments: `${API}/payments${qs}`,
        batches: `${API}/reconciliation-batches`,
        webhooks: `${API}/webhook-endpoints`,
        deliveries: `${API}/webhook-deliveries`,
        holds: `${API}/partner-holds`,
        vault: `${API}/saved-payment-methods`,
        events: `${API}/gateway-events${qs}`,
      };
      const path = paths[tab] || paths.transactions;
      const r = await fetch(path, { headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setRows(j.items || []);
      if (tab === "webhooks") setWebhooks(j.items || []);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
      setRows([]);
      setSummary(null);
    } finally {
      setLoading(false);
    }
  }, [token, headers, orderFilter, tab]);

  useEffect(() => {
    void load();
  }, [load]);

  const onSeed = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seed`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Seed aplicado.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seed`));
    } finally {
      setLoading(false);
    }
  };

  const onRetryDelivery = async (deliveryId) => {
    if (!token || !canMutate) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/webhook-deliveries/${encodeURIComponent(deliveryId)}/retry`, {
        method: "POST",
        headers,
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Retry ${deliveryId}`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onRotate = async () => {
    if (!token || !canMutate || !selectedWebhook) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/webhook-endpoints/${encodeURIComponent(selectedWebhook)}/rotate-secret`, {
        method: "POST",
        headers,
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setLastSecret(j.secret || "");
      setOk("Secret rotacionado — copie agora.");
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/webhook-endpoints/.../rotate-secret`));
    } finally {
      setLoading(false);
    }
  };

  const tableRows = rows.map((row) => {
    const id = row.id || row.code || row.player_code || row.rule_code || row.corridor_code || "—";
    let detalhe = "";
    if (tab === "ecosystem") {
      const pri = row.metadata_json?.payment_priority ? " ★" : "";
      detalhe = `${row.segment} · ${JSON.stringify(row.countries_json)} · ${row.integration_status}${pri}`;
    } else if (tab === "segments") detalhe = `${row.name} · ${row.default_protocol}`;
    else if (tab === "integrations")
      detalhe = `score ${row.readiness_score} · ${row.payment_capture_mode} · prod=${row.production_ready ? "Y" : "N"}`;
    else if (tab === "coverage")
      detalhe = `${row.country_code} · ${row.coverage_role} · ${row.locker_density}`;
    else if (tab === "milestones") detalhe = `${row.player_code} · ${row.phase} · ${row.status}`;
    else if (tab === "corridors")
      detalhe = `${row.origin_country}→${row.destination_country} · ${row.fee_basis_points}bps`;
    else if (tab === "compliance")
      detalhe = `${row.country_code} · ${row.regulatory_framework} · ${row.risk_tier}`;
    else if (tab === "routing")
      detalhe = `${row.country_code} · ${row.payment_method} → ${row.primary_player_code}`;
    else if (tab === "incidents") detalhe = `${row.severity} · ${row.status} · ${row.title}`;
    else if (tab === "cross-domain") {
      if (row._kind === "gap") detalhe = row.detalhe || row.message;
      else if (row._kind === "obligation")
        detalhe = `${row.domain_code} · ${row.obligation_type} · ${row.status}`;
      else detalhe = `${row.external_domain} · ${row.external_entity_type} → ${row.external_entity_id}`;
    } else if (tab === "relations") detalhe = `${row.from_player_code} → ${row.to_player_code} · ${row.relation_type}`;
    else if (tab === "order-context")
      detalhe = `${row.order_id} · ${row.locker_network_code} · ${row.status}`;
    else if (tab === "transactions")
      detalhe = `${row.order_id} · ${row.gateway} · ${row.payment_method} · ${row.status}`;
    else if (tab === "instructions") detalhe = `${row.order_id} · ${row.instruction_type}`;
    else if (tab === "splits") detalhe = `${row.order_id} · ${row.recipient_type}`;
    else if (tab === "payments") detalhe = `${row.order_id} · ${row.provider}`;
    else if (tab === "batches") detalhe = `${row.batch_code} · ${row.status}`;
    else if (tab === "webhooks") detalhe = `${row.partner_type} · ${row.url}`;
    else if (tab === "deliveries") detalhe = `${row.event_name} · ${row.status}`;
    else if (tab === "holds") detalhe = `${row.partner_id} · ${row.hold_amount_cents}c`;
    else if (tab === "vault") detalhe = `${row.user_id} · ****${row.last4}`;
    else detalhe = `${row.event_type} · ${row.locker_id}`;
    return { key: id, id, detalhe, status: row.status, rawId: row.id };
  });

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10, gap: 8 }}>
          <Link to="/ops/payment-gateway/admin" style={crossShortcutLinkStyle}>
            Payment Gateway
          </Link>
          <Link to="/ops/payments/reconciliation" style={crossShortcutLinkStyle}>
            Conciliacao
          </Link>
          <Link to="/ops/money-cambio/admin" style={crossShortcutLinkStyle}>
            Money &amp; Cambio
          </Link>
          <Link to="/ops/order-pickup/admin" style={crossShortcutLinkStyle}>
            Order Pickup
          </Link>
          <Link to="/ops/finance/admin" style={crossShortcutLinkStyle}>
            Finance OPS
          </Link>
          <Link to="/ops/marketplace/admin" style={crossShortcutLinkStyle}>
            Marketplace
          </Link>
        </div>

        <OpsPageTitleHeader
          title="OPS — Payments (mundial · cross-domain)"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Transacoes, instrucoes, splits, payments, webhooks e gateway_events —{" "}
          <code style={{ color: "#e2e8f0" }}>{API}</code>
        </p>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Dominio PAYMENT</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {TABS.map(([k, label]) => (
                <button key={k} type="button" style={tabButtonStyle(tab === k)} onClick={() => setTab(k)}>
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div style={healthLocalFilterRowStyle}>
            <label style={healthLocalFilterFieldStyle}>
              order_id
              <input
                value={orderFilter}
                onChange={(e) => setOrderFilter(e.target.value)}
                style={healthLocalFilterInputStyle}
                placeholder="ORD-DEMO-INPOST-001"
              />
            </label>
          </div>

          {tab === "webhooks" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                endpoint
                <select
                  value={selectedWebhook}
                  onChange={(e) => setSelectedWebhook(e.target.value)}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="">— selecione —</option>
                  {webhooks.map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.id} ({w.partner_type})
                    </option>
                  ))}
                </select>
              </label>
            </div>
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
                {tab === "webhooks" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onRotate()}
                    disabled={loading || !selectedWebhook}
                  >
                    Rotacionar secret
                  </button>
                ) : null}
              </>
            ) : null}
          </div>
          <p style={summary24hHintStyle}>
            Seed demo: InPost/Magalu/DPD — order <code>ORD-DEMO-INPOST-001</code>. Catálogo em Payment Gateway; FX em Money OPS.
          </p>
        </section>

        {lastSecret ? (
          <p style={apiKeyBannerStyle}>
            webhook secret: <code>{lastSecret}</code>
          </p>
        ) : null}

        {err ? (
          <div style={criticalBannerStyle} role="alert">
            {err}
          </div>
        ) : null}
        {ok ? <p style={okBannerStyle}>{ok}</p> : null}
        {!token ? <p style={summary24hHintStyle}>Faca login com perfil admin_operacao.</p> : null}

        {tab === "cross-domain" && summary ? (
          <section style={opsSanityCardStyle}>
            <p style={summary24hHintStyle}>
              Domínios: {summary.registry_total} · Gaps: {summary.gaps_total} · Obrigações pendentes:{" "}
              {summary.obligations_pending}
            </p>
          </section>
        ) : null}

        {tab === "intelligence" && summary ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>KPIs PAYMENT</h3>
            </div>
            <p style={summary24hHintStyle}>
              TX {summary.transactions_approved}/{summary.transactions_total} · recon pendente{" "}
              {summary.reconciliation_pending} · WH pendente {summary.webhook_pending} · players LIVE{" "}
              {summary.ecosystem_players_live}
            </p>
            <pre style={{ fontSize: 11, overflow: "auto" }}>{JSON.stringify(summary.segments, null, 2)}</pre>
          </section>
        ) : null}

        {tab === "intelligence" && orderGraph ? (
          <section style={opsSanityCardStyle}>
            <pre style={{ fontSize: 10, overflow: "auto", maxHeight: 320 }}>{JSON.stringify(orderGraph, null, 2)}</pre>
          </section>
        ) : null}

        {(tab === "graph" || tab === "intelligence") && ecosystemGraph ? (
          <PaymentsEcosystemGraph
            graph={ecosystemGraph}
            loading={loading}
            error={err}
            height={tab === "graph" ? 640 : 360}
          />
        ) : null}

        {tab === "milestones" && canMutate ? (
          <PaymentsMilestoneCrud
            headers={headers}
            rows={rows}
            onRefresh={() => void load()}
            onOk={setOk}
            onErr={setErr}
          />
        ) : null}

        {tab === "routing" && canMutate ? (
          <PaymentsRoutingCrud
            headers={headers}
            rows={rows}
            onRefresh={() => void load()}
            onOk={setOk}
            onErr={setErr}
          />
        ) : null}

        {(tab === "cross-domain" || (tab !== "intelligence" && tab !== "graph")) && tableRows.length > 0 ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>
                {TABS.find(([k]) => k === tab)?.[1] || tab} ({tableRows.length})
              </h3>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["id", "detalhe", tab === "deliveries" ? "acao" : null].filter(Boolean).map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tableRows.map((row) => (
                    <tr key={row.key}>
                      <td style={tdStyle}>
                        <code>{row.id}</code>
                      </td>
                      <td style={tdStyle}>{row.detalhe}</td>
                      {tab === "deliveries" ? (
                        <td style={tdStyle}>
                          {row.status === "PENDING" ? (
                            <button type="button" style={buttonGhostStyle} onClick={() => void onRetryDelivery(row.rawId)}>
                              retry
                            </button>
                          ) : null}
                        </td>
                      ) : null}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}
      </section>
    </div>
  );
}


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
  mutedTextStyle,
  okBannerStyle,
  pageStyle,
  tabButtonStyle,
  tableStyle,
  tdStyle,
  thStyle,
  toolbarStyle,
} from "../styles/opsShellStyles";

const BASE = import.meta.env.VITE_HARDWARE_ADMIN_BASE_URL || "/api/hwa";
const API = `${BASE}/v1/hardware-admin`;
const PAGE_VERSION = "ops/hardware/admin v0.1";

function parseError(payload, fallback = "Falha na API hardware-admin.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  return fallback;
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao (${endpoint}). Verifique proxy ${BASE} (porta 8025).`;
  }
  return raw;
}

const TABS = [
  "dashboard",
  "vendors",
  "ecosystem",
  "marketplace",
  "payments",
  "carriers",
  "assets",
  "finance",
  "operators",
  "runtime",
  "topology",
  "references",
  "channels",
  "ops",
];

export default function OpsHardwareAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [searchParams, setSearchParams] = useSearchParams();
  const rawTab = searchParams.get("tab") || "dashboard";
  const tab = TABS.includes(rawTab) ? rawTab : "dashboard";
  const setTab = (t) => {
    const p = new URLSearchParams(searchParams);
    if (t === "dashboard") p.delete("tab");
    else p.set("tab", t);
    setSearchParams(p, { replace: true });
  };
  const [dashboard, setDashboard] = useState(null);
  const [vendors, setVendors] = useState([]);
  const [assets, setAssets] = useState([]);
  const [ecosystem, setEcosystem] = useState([]);
  const [marketplace, setMarketplace] = useState([]);
  const [payments, setPayments] = useState([]);
  const [carriers, setCarriers] = useState([]);
  const [capex, setCapex] = useState([]);
  const [opex, setOpex] = useState([]);
  const [operators, setOperators] = useState([]);
  const [runtime, setRuntime] = useState([]);
  const [features, setFeatures] = useState([]);
  const [slots, setSlots] = useState([]);
  const [references, setReferences] = useState([]);
  const [integrationHub, setIntegrationHub] = useState(null);
  const [segments, setSegments] = useState([]);
  const [capabilities, setCapabilities] = useState([]);
  const [playerRelations, setPlayerRelations] = useState([]);
  const [channelBindings, setChannelBindings] = useState([]);
  const [readinessRows, setReadinessRows] = useState([]);
  const [marketplaceBridge, setMarketplaceBridge] = useState([]);
  const [devices, setDevices] = useState([]);
  const [syncQueue, setSyncQueue] = useState([]);
  const [telemetry, setTelemetry] = useState([]);
  const [vendorForm, setVendorForm] = useState({ name: "", code: "", vendor_type: "LOCKER_NETWORK" });
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
      const [dash, v, a, eco, mkt, pay, car, cap, opx, o, r, feat, sl, ref, hub, seg, caps, rels, ch, ready, bridge, d, s, t] = await Promise.all([
        fetch(`${API}/cross-domain/dashboard`, { headers }),
        fetch(`${API}/hardware-vendors`, { headers }),
        fetch(`${API}/hardware-assets`, { headers }),
        fetch(`${API}/cross-domain/ecosystem-players`, { headers }),
        fetch(`${API}/cross-domain/marketplace-links`, { headers }),
        fetch(`${API}/cross-domain/payment-bindings`, { headers }),
        fetch(`${API}/cross-domain/carrier-bindings`, { headers }),
        fetch(`${API}/locker-capex`, { headers }),
        fetch(`${API}/locker-opex`, { headers }),
        fetch(`${API}/locker-operators`, { headers }),
        fetch(`${API}/runtime-lockers`, { headers }),
        fetch(`${API}/locker-features`, { headers }),
        fetch(`${API}/locker-slots`, { headers }),
        fetch(`${API}/cross-domain/domain-references`, { headers }),
        fetch(`${API}/integration-hub/summary`, { headers }),
        fetch(`${API}/integration-hub/segments`, { headers }),
        fetch(`${API}/integration-hub/capabilities`, { headers }),
        fetch(`${API}/integration-hub/player-relations`, { headers }),
        fetch(`${API}/integration-hub/channel-bindings`, { headers }),
        fetch(`${API}/integration-hub/integration-readiness`, { headers }),
        fetch(`${API}/integration-hub/marketplace-bridge`, { headers }),
        fetch(`${API}/hardware-ops/devices`, { headers }),
        fetch(`${API}/hardware-ops/sync-queue`, { headers }),
        fetch(`${API}/hardware-ops/telemetry`, { headers }),
      ]);
      const dj = await dash.json().catch(() => ({}));
      const vj = await v.json().catch(() => ({}));
      const aj = await a.json().catch(() => ({}));
      const ecoj = await eco.json().catch(() => ({}));
      const mktj = await mkt.json().catch(() => ({}));
      const payj = await pay.json().catch(() => ({}));
      const carj = await car.json().catch(() => ({}));
      const capj = await cap.json().catch(() => ({}));
      const opxj = await opx.json().catch(() => ({}));
      const oj = await o.json().catch(() => ({}));
      const rj = await r.json().catch(() => ({}));
      const featj = await feat.json().catch(() => ({}));
      const slj = await sl.json().catch(() => ({}));
      const refj = await ref.json().catch(() => ({}));
      const hubj = await hub.json().catch(() => ({}));
      const segj = await seg.json().catch(() => ({}));
      const capsj = await caps.json().catch(() => ({}));
      const relsj = await rels.json().catch(() => ({}));
      const chj = await ch.json().catch(() => ({}));
      const readyj = await ready.json().catch(() => ({}));
      const bridgej = await bridge.json().catch(() => ({}));
      const devj = await d.json().catch(() => ({}));
      const sj = await s.json().catch(() => ({}));
      const tj = await t.json().catch(() => ({}));
      if (!v.ok) throw new Error(parseError(vj));
      setDashboard(dj);
      setVendors(vj.vendors || []);
      setAssets(aj.items || []);
      setEcosystem(ecoj.items || []);
      setMarketplace(mktj.items || []);
      setPayments(payj.items || []);
      setCarriers(carj.items || []);
      setCapex(capj.items || []);
      setOpex(opxj.items || []);
      setOperators(oj.items || []);
      setRuntime(rj.items || []);
      setFeatures(featj.items || []);
      setSlots(slj.items || []);
      setReferences(refj.items || []);
      setIntegrationHub(hubj.segments !== undefined ? hubj : null);
      setSegments(segj.items || []);
      setCapabilities(capsj.items || []);
      setPlayerRelations(relsj.items || []);
      setChannelBindings(chj.items || []);
      setReadinessRows(readyj.items || []);
      setMarketplaceBridge(bridgej.items || []);
      setDevices(devj.items || []);
      setSyncQueue(sj.items || []);
      setTelemetry(tj.items || []);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
      setDashboard(null);
      setVendors([]);
      setAssets([]);
      setEcosystem([]);
      setMarketplace([]);
      setPayments([]);
      setCarriers([]);
      setCapex([]);
      setOpex([]);
      setOperators([]);
      setRuntime([]);
      setFeatures([]);
      setSlots([]);
      setReferences([]);
      setIntegrationHub(null);
      setSegments([]);
      setCapabilities([]);
      setPlayerRelations([]);
      setChannelBindings([]);
      setReadinessRows([]);
      setMarketplaceBridge([]);
      setDevices([]);
      setSyncQueue([]);
      setTelemetry([]);
    } finally {
      setLoading(false);
    }
  }, [token, headers]);

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

  const onCreateVendor = async () => {
    if (!token || !canMutate || !vendorForm.name || !vendorForm.code) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/hardware-vendors`, {
        method: "POST",
        headers,
        body: JSON.stringify(vendorForm),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Vendor ${j.code} criado.`);
      setSelectedId(j.id);
      setVendorForm({ name: "", code: "", vendor_type: "LOCKER_NETWORK" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/hardware-vendors`));
    } finally {
      setLoading(false);
    }
  };

  const onWebhook = async () => {
    if (!token || !canMutate || !selectedId || !webhookUrl) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/hardware-vendors/${encodeURIComponent(selectedId)}/webhook`, {
        method: "PUT",
        headers,
        body: JSON.stringify({
          url: webhookUrl,
          secret: webhookSecret || undefined,
          events: ["locker.*", "telemetry.*"],
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Webhook salvo para ${selectedId}.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/hardware-vendors/.../webhook`));
    } finally {
      setLoading(false);
    }
  };

  const onRotate = async () => {
    if (!token || !canMutate || !selectedId) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/hardware-vendors/${encodeURIComponent(selectedId)}/api-keys/rotate`, {
        method: "POST",
        headers,
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setLastApiKey(j.api_key || "");
      setOk(`Nova API key (${j.key_prefix}…). Copie agora.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/hardware-vendors/.../api-keys/rotate`));
    } finally {
      setLoading(false);
    }
  };

  const tableRows =
    tab === "dashboard" && dashboard
      ? [{ key: "dash", id: "KPIs", detalhe: `vendors ${dashboard.vendors} · ecosystem ${dashboard.ecosystem_players} · mkt ${dashboard.marketplace_links} · pay ${dashboard.payment_bindings} · carriers ${dashboard.carrier_bindings} · sync ${dashboard.sync_pending}` }]
      : tab === "vendors"
        ? vendors.map((v) => ({ key: v.id, id: v.code, detalhe: `${v.name} · ${v.vendor_type} · ${v.active ? "ativo" : "inativo"}` }))
        : tab === "ecosystem"
          ? ecosystem.map((p) => ({ key: p.id, id: p.player_code, detalhe: `${p.name} · ${p.segment} · mkt ${p.marketplace_channel_code || "—"}` }))
          : tab === "marketplace"
            ? marketplace.map((m) => ({ key: m.id, id: m.channel_code, detalhe: `${m.seller_name || m.seller_id} · locker ${m.locker_id || "—"}` }))
            : tab === "payments"
              ? payments.map((p) => ({ key: p.id, id: p.payment_method_code, detalhe: `${p.locker_id} · ${p.payment_provider_code || "—"}` }))
              : tab === "carriers"
                ? carriers.map((c) => ({ key: c.id, id: c.carrier_code, detalhe: `${c.carrier_name} · ${c.locker_id} · ${c.country_code}` }))
                : tab === "assets"
                  ? assets.map((a) => ({ key: a.id, id: a.asset_code, detalhe: `${a.asset_category} · ${a.description} · ${a.status}` }))
                  : tab === "finance"
                    ? [...capex.map((c) => ({ key: c.id, id: c.locker_id, detalhe: `CAPEX ${c.acquisition_cost_cents}c · ${c.status}` })), ...opex.map((x) => ({ key: x.id, id: x.cost_type, detalhe: `OPEX ${x.locker_id} · ${x.amount_cents}c` }))]
                    : tab === "operators"
                      ? operators.map((o) => ({ key: o.id, id: o.name, detalhe: `${o.operator_type} · ${o.country} · ${o.status}` }))
                      : tab === "runtime"
                        ? runtime.map((l) => ({ key: l.locker_id, id: l.locker_id, detalhe: `${l.display_name} · ${l.slot_count_total} slots · mqtt ${l.mqtt_locker_id}` }))
                        : tab === "topology"
                          ? [...features.map((f) => ({ key: f.locker_id, id: f.locker_id, detalhe: `kiosk ${f.supports_kiosk} ble ${f.supports_ble} nfc ${f.supports_nfc}` })), ...slots.map((s) => ({ key: s.id, id: `slot ${s.slot_number}`, detalhe: `${s.locker_id} · ${s.slot_size}` }))]
                          : tab === "references"
                            ? references.map((r) => ({ key: r.id, id: r.domain_type, detalhe: `${r.external_id} · ${r.external_code || "—"}` }))
                            : tab === "channels"
                              ? [
                                  ...(integrationHub
                                    ? [{ key: "hub", id: "Integration Hub", detalhe: `score ${integrationHub.avg_score} · GO_LIVE ${integrationHub.bands?.GO_LIVE ?? 0} · sync ${integrationHub.capabilities_in_sync} · gaps ${integrationHub.marketplace_capability_gaps}` }]
                                    : []),
                                  ...readinessRows.map((x) => ({ key: x.player_id, id: x.player_code, detalhe: `${x.readiness_band} · score ${x.score_total} · caps ${x.capability_count}` })),
                                  ...marketplaceBridge.map((x) => ({ key: x.hardware_player_code, id: x.hardware_player_code, detalhe: `mkt ${x.marketplace_partner_code} · sync ${x.in_sync ? "Y" : "N"} · ${x.capabilities_db}/${x.capabilities_expected}` })),
                                  ...segments.map((x) => ({ key: x.code, id: x.code, detalhe: `${x.name} · ${x.parent_group}` })),
                                  ...capabilities.map((x) => ({ key: x.id, id: x.capability_code, detalhe: `${x.player_code} · ${x.protocol} · ${x.target_domain}` })),
                                  ...playerRelations.map((x) => ({ key: x.id, id: x.relation_type, detalhe: `${x.from_player_code} → ${x.to_player_code}` })),
                                  ...channelBindings.map((x) => ({ key: x.id, id: x.channel_type, detalhe: `${x.locker_id} · ${x.player_code} · ${x.integration_mode}` })),
                                ]
                              : [
                                ...devices.map((d) => ({ key: d.device_hash, id: String(d.device_hash).slice(0, 18), detalhe: `${d.locker_id || "—"} · seen ${d.seen_count}` })),
                                ...syncQueue.map((s) => ({ key: s.id, id: s.operation, detalhe: `${s.locker_id} · ${s.status}` })),
                                ...telemetry.map((x) => ({ key: x.id, id: x.event_type, detalhe: `${x.locker_id} · ${x.severity}` })),
                              ];

  const listCount = tableRows.length;

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader
          title="Hardware OPS"
          subtitle="Redes locker (SwipBox, Cleveron, Pickup PL…), ativos CAPEX, operadores, runtime MQTT, telemetria."
          version={PAGE_VERSION}
        />
        <div style={toolbarStyle}>
          <button type="button" style={buttonGhostStyle} onClick={() => void load()} disabled={loading}>
            Atualizar
          </button>
          {canMutate && (
            <button type="button" style={buttonPrimaryStyle} onClick={() => void onSeed()} disabled={loading}>
              Seed demo
            </button>
          )}
        </div>
        {err && <div style={criticalBannerStyle}>{err}</div>}
        {ok && <div style={okBannerStyle}>{ok}</div>}
        {lastApiKey && <div style={apiKeyBannerStyle}>API key: {lastApiKey}</div>}
        <p style={mutedTextStyle}>{loading ? "Carregando…" : `${listCount} registro(s) na aba atual.`}</p>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
          {[
            ["dashboard", "Dashboard"],
            ["vendors", "Vendors"],
            ["ecosystem", "Ecossistema"],
            ["marketplace", "Marketplace"],
            ["payments", "Payments"],
            ["carriers", "Carriers"],
            ["assets", "Ativos"],
            ["finance", "CAPEX/OPEX"],
            ["operators", "Operadores"],
            ["runtime", "Runtime"],
            ["topology", "Topology"],
            ["references", "Refs"],
            ["channels", "Integration Hub"],
            ["ops", "Ops"],
          ].map(([t, label]) => (
            <button key={t} type="button" style={tabButtonStyle(tab === t)} onClick={() => setTab(t)}>
              {label}
            </button>
          ))}
        </div>

        {tab === "vendors" && canMutate && (
          <div style={{ display: "grid", gap: 8, marginBottom: 12 }}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              <input
                placeholder="Nome vendor"
                value={vendorForm.name}
                onChange={(e) => setVendorForm({ ...vendorForm, name: e.target.value })}
              />
              <input
                placeholder="Codigo"
                value={vendorForm.code}
                onChange={(e) => setVendorForm({ ...vendorForm, code: e.target.value })}
              />
              <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreateVendor()}>
                Criar vendor
              </button>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
                <option value="">Vendor para webhook/API key</option>
                {vendors.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.code}
                  </option>
                ))}
              </select>
              <input placeholder="Webhook URL" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} />
              <input placeholder="Secret" value={webhookSecret} onChange={(e) => setWebhookSecret(e.target.value)} />
              <button type="button" style={buttonGhostStyle} onClick={() => void onWebhook()}>
                Webhook
              </button>
              <button type="button" style={buttonGhostStyle} onClick={() => void onRotate()}>
                Rotacionar API key
              </button>
            </div>
          </div>
        )}

        {tab !== "dashboard" && (
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>ID</th>
              <th style={thStyle}>Detalhe</th>
            </tr>
          </thead>
          <tbody>
            {tableRows.map((row) => (
              <tr key={row.key}>
                <td style={tdStyle}>{row.id}</td>
                <td style={tdStyle}>{row.detalhe}</td>
              </tr>
            ))}
            {!tableRows.length && (
              <tr>
                <td colSpan={2} style={tdStyle}>
                  Nenhum registro — Atualizar ou Seed.
                </td>
              </tr>
            )}
          </tbody>
        </table>
        )}
      </section>
    </div>
  );
}

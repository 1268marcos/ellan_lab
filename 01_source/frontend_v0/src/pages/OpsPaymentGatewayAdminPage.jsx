
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

const BASE = import.meta.env.VITE_PAYMENT_GATEWAY_ADMIN_BASE_URL || "/api/pga";
const API = `${BASE}/v1/payment-gateway-admin`;
const PAGE_VERSION = "ops/payment-gateway/admin v0.1";

function parseError(payload, fallback = "Falha na API payment-gateway-admin.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  return fallback;
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao (${endpoint}). Verifique proxy ${BASE} (porta 8017).`;
  }
  return raw;
}

export default function OpsPaymentGatewayAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [tab, setTab] = useState("catalog");
  const [methods, setMethods] = useState([]);
  const [providers, setProviders] = useState([]);
  const [devices, setDevices] = useState([]);
  const [idem, setIdem] = useState([]);
  const [risk, setRisk] = useState([]);
  const [methodForm, setMethodForm] = useState({ code: "", name: "" });
  const [pspForm, setPspForm] = useState({ name: "", code: "", provider_type: "STRIPE" });
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
      const [m, p, d, i, r] = await Promise.all([
        fetch(`${API}/payment-method-catalog`, { headers }),
        fetch(`${API}/payment-provider-partners`, { headers }),
        fetch(`${API}/gateway-ops/devices`, { headers }),
        fetch(`${API}/gateway-ops/idempotency-keys`, { headers }),
        fetch(`${API}/gateway-ops/risk-events`, { headers }),
      ]);
      const mj = await m.json().catch(() => ({}));
      const pj = await p.json().catch(() => ({}));
      const dj = await d.json().catch(() => ({}));
      const ij = await i.json().catch(() => ({}));
      const rj = await r.json().catch(() => ({}));
      if (!m.ok) throw new Error(parseError(mj));
      if (!p.ok) throw new Error(parseError(pj));
      setMethods(mj.items || []);
      setProviders(pj.partners || []);
      setDevices(dj.items || []);
      setIdem(ij.items || []);
      setRisk(rj.items || []);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
      setMethods([]);
      setProviders([]);
      setDevices([]);
      setIdem([]);
      setRisk([]);
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
      setOk("Seed aplicado.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seed`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateMethod = async () => {
    if (!token || !canMutate || !methodForm.code || !methodForm.name) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/payment-method-catalog`, {
        method: "POST",
        headers,
        body: JSON.stringify(methodForm),
      });
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

  const onCreatePsp = async () => {
    if (!token || !canMutate || !pspForm.name || !pspForm.code) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/payment-provider-partners`, {
        method: "POST",
        headers,
        body: JSON.stringify(pspForm),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`PSP ${j.code} criado.`);
      setSelectedId(j.id);
      setPspForm({ name: "", code: "", provider_type: "STRIPE" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/payment-provider-partners`));
    } finally {
      setLoading(false);
    }
  };

  const onWebhook = async () => {
    if (!token || !canMutate || !selectedId || !webhookUrl) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/payment-provider-partners/${encodeURIComponent(selectedId)}/webhook`, {
        method: "PUT",
        headers,
        body: JSON.stringify({
          url: webhookUrl,
          secret: webhookSecret || undefined,
          events: ["payment.completed", "payment.failed"],
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Webhook salvo para ${selectedId}.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/payment-provider-partners/.../webhook`));
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
        `${API}/payment-provider-partners/${encodeURIComponent(selectedId)}/api-keys/rotate`,
        { method: "POST", headers },
      );
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setLastApiKey(j.api_key || "");
      setOk(`Nova API key (${j.key_prefix}…). Copie agora.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/payment-provider-partners/.../api-keys/rotate`));
    } finally {
      setLoading(false);
    }
  };

  const onPurgeIdem = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/gateway-ops/idempotency-keys/purge-expired`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Idempotencia expirada removida: ${j.purged ?? 0}.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/gateway-ops/idempotency-keys/purge-expired`));
    } finally {
      setLoading(false);
    }
  };

  const tableRows =
    tab === "catalog"
      ? methods.map((m) => ({ key: `m-${m.id}`, tipo: "method", id: m.code, detalhe: `${m.name} · ${m.is_active ? "ativo" : "inativo"}` }))
      : tab === "providers"
        ? providers.map((p) => ({
            key: `p-${p.id}`,
            tipo: "psp",
            id: p.code,
            detalhe: `${p.name} · ${p.provider_type} · ${p.active ? "ativo" : "inativo"}`,
          }))
        : [
            ...devices.map((d) => ({
              key: `d-${d.device_hash}`,
              tipo: "device",
              id: String(d.device_hash).slice(0, 20),
              detalhe: `${d.locker_id || "—"} · seen ${d.seen_count}`,
            })),
            ...idem.map((x) => ({ key: `i-${x.id}`, tipo: "idem", id: x.id, detalhe: x.status })),
            ...risk.map((x) => ({
              key: `r-${x.id}`,
              tipo: "risk",
              id: x.id,
              detalhe: `${x.decision} · score ${x.score}`,
            })),
          ];

  const listCount =
    tab === "catalog" ? methods.length : tab === "providers" ? providers.length : devices.length + idem.length + risk.length;

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10, gap: 8 }}>
          <Link to="/ops/tenants/admin" style={crossShortcutLinkStyle}>
            Tenants
          </Link>
          <Link to="/ops/partners/admin" style={crossShortcutLinkStyle}>
            Parceiros
          </Link>
          <Link to="/ops/access/user-roles" style={crossShortcutLinkStyle}>
            user_roles
          </Link>
          <Link to="/ops/partners/dashboard" style={crossShortcutLinkStyle}>
            Partners dashboard
          </Link>
        </div>

        <OpsPageTitleHeader
          title="OPS — Payment Gateway (admin)"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Catalogo de metodos, PSP/adquirentes, webhook, API key, device registry, idempotencia e risk —{" "}
          <code style={{ color: "#e2e8f0" }}>{API}</code> — role{" "}
          <code style={{ color: "#e2e8f0" }}>admin_operacao</code> para escrita.
        </p>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Area de cadastro</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button type="button" style={tabButtonStyle(tab === "catalog")} onClick={() => setTab("catalog")}>
                Catalogo
              </button>
              <button type="button" style={tabButtonStyle(tab === "providers")} onClick={() => setTab("providers")}>
                PSP / Adquirente
              </button>
              <button type="button" style={tabButtonStyle(tab === "ops")} onClick={() => setTab("ops")}>
                Operacoes gateway
              </button>
            </div>
          </div>

          {tab === "catalog" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                code
                <input
                  value={methodForm.code}
                  onChange={(e) => setMethodForm((f) => ({ ...f, code: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="PIX"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                name
                <input
                  value={methodForm.name}
                  onChange={(e) => setMethodForm((f) => ({ ...f, name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="PIX instantaneo"
                />
              </label>
            </div>
          ) : null}

          {tab === "providers" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                name
                <input
                  value={pspForm.name}
                  onChange={(e) => setPspForm((f) => ({ ...f, name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                code
                <input
                  value={pspForm.code}
                  onChange={(e) => setPspForm((f) => ({ ...f, code: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                provider_type
                <select
                  value={pspForm.provider_type}
                  onChange={(e) => setPspForm((f) => ({ ...f, provider_type: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="STRIPE">STRIPE</option>
                  <option value="MERCADOPAGO">MERCADOPAGO</option>
                  <option value="OTHER">OTHER</option>
                </select>
              </label>
            </div>
          ) : null}

          {tab === "ops" ? (
            <p style={summary24hHintStyle}>
              Device registry, chaves de idempotencia e eventos de risco (somente listagem e purge de expirados).
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
                {tab === "catalog" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreateMethod()}
                    disabled={loading || !methodForm.code || !methodForm.name}
                  >
                    Criar metodo
                  </button>
                ) : null}
                {tab === "providers" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreatePsp()}
                    disabled={loading || !pspForm.name || !pspForm.code}
                  >
                    Criar PSP
                  </button>
                ) : null}
                {tab === "ops" ? (
                  <button type="button" style={buttonGhostStyle} onClick={() => void onPurgeIdem()} disabled={loading}>
                    Purgar idempotencia expirada
                  </button>
                ) : null}
              </>
            ) : null}
          </div>
        </section>

        {tab === "providers" ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Webhook e API key (PSP)</h3>
            </div>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                provider_id
                <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} style={healthLocalFilterInputStyle}>
                  <option value="">— selecione —</option>
                  {providers.map((p) => (
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
              <h3 style={{ margin: 0, fontSize: 14 }}>
                {tab === "catalog"
                  ? `Metodos de pagamento (${methods.length})`
                  : tab === "providers"
                    ? `PSP / adquirentes (${providers.length})`
                    : `Gateway ops (devices: ${devices.length}, idem: ${idem.length}, risk: ${risk.length})`}
              </h3>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["tipo", "code / id", "detalhe"].map((h) => (
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
        ) : null}
      </section>
    </div>
  );
}

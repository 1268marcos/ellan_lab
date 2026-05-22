import React, { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import {
  apiKeyBannerStyle,
  buttonGhostStyle,
  buttonPrimaryStyle,
  cardStyle,
  crossShortcutLinkStyle,
  mutedTextStyle,
  okBannerStyle,
  pageStyle,
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
  const [methodCode, setMethodCode] = useState("");
  const [methodName, setMethodName] = useState("");
  const [pspName, setPspName] = useState("");
  const [pspCode, setPspCode] = useState("");
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
    } finally {
      setLoading(false);
    }
  }, [token, headers]);

  const onSeed = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/seed`, { method: "POST", headers });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(parseError(json));
      setOk("Seed aplicado.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seed`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateMethod = async (e) => {
    e.preventDefault();
    if (!canMutate) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/payment-method-catalog`, {
        method: "POST",
        headers,
        body: JSON.stringify({ code: methodCode, name: methodName }),
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(parseError(json));
      setOk(`Metodo ${methodCode} criado.`);
      setMethodCode("");
      setMethodName("");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onCreatePsp = async (e) => {
    e.preventDefault();
    if (!canMutate) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/payment-provider-partners`, {
        method: "POST",
        headers,
        body: JSON.stringify({ name: pspName, code: pspCode, provider_type: "STRIPE" }),
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(parseError(json));
      setOk(`PSP ${json.code} criado.`);
      setSelectedId(json.id);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onWebhook = async () => {
    if (!selectedId || !webhookUrl) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/payment-provider-partners/${encodeURIComponent(selectedId)}/webhook`, {
        method: "PUT",
        headers,
        body: JSON.stringify({ url: webhookUrl, secret: webhookSecret || undefined }),
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(parseError(json));
      setOk("Webhook salvo.");
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onRotateKey = async () => {
    if (!selectedId) return;
    setLoading(true);
    try {
      const res = await fetch(
        `${API}/payment-provider-partners/${encodeURIComponent(selectedId)}/api-keys/rotate`,
        { method: "POST", headers },
      );
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(parseError(json));
      setLastApiKey(json.api_key);
      setOk(`Nova API key (${json.key_prefix}…).`);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={pageStyle}>
      <OpsPageTitleHeader
        title="OPS / Payment Gateway"
        subtitle="Catalogo, PSP, device registry, idempotencia e risk events."
        version={PAGE_VERSION}
      />
      <div style={toolbarStyle}>
        <button type="button" style={buttonGhostStyle} disabled={loading || !canMutate} onClick={() => void onSeed()}>
          Seed
        </button>
        <button type="button" style={buttonPrimaryStyle} disabled={loading} onClick={() => void load()}>
          Atualizar
        </button>
        <Link to="/ops/partners/admin" style={crossShortcutLinkStyle}>
          Parceiros e-commerce
        </Link>
      </div>
      {err ? <p style={{ color: "#b91c1c" }}>{err}</p> : null}
      {ok ? <p style={okBannerStyle}>{ok}</p> : null}
      {lastApiKey ? <p style={apiKeyBannerStyle}>API key: {lastApiKey}</p> : null}
      <p style={mutedTextStyle}>{loading ? "Processando…" : null}</p>

      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        {["catalog", "providers", "ops"].map((t) => (
          <button
            key={t}
            type="button"
            style={tabButtonStyle(tab === t)}
            onClick={() => setTab(t)}
          >
            {t === "catalog" ? "Catalogo" : t === "providers" ? "PSP" : "Operacoes"}
          </button>
        ))}
      </div>

      <div style={cardStyle}>
        {tab === "catalog" ? (
          <form onSubmit={onCreateMethod}>
            <input
              placeholder="Codigo"
              value={methodCode}
              onChange={(e) => setMethodCode(e.target.value)}
              required
            />
            <input
              placeholder="Nome"
              value={methodName}
              onChange={(e) => setMethodName(e.target.value)}
              required
            />
            <button type="submit" disabled={!canMutate}>
              Criar metodo
            </button>
          </form>
        ) : null}
        {tab === "providers" ? (
          <>
            <form onSubmit={onCreatePsp}>
              <input placeholder="Nome PSP" value={pspName} onChange={(e) => setPspName(e.target.value)} required />
              <input placeholder="Codigo" value={pspCode} onChange={(e) => setPspCode(e.target.value)} required />
              <button type="submit" disabled={!canMutate}>
                Criar PSP
              </button>
            </form>
            <div style={{ marginTop: 12, display: "flex", flexWrap: "wrap", gap: 8 }}>
              <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
                <option value="">PSP</option>
                {providers.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.code}
                  </option>
                ))}
              </select>
              <input placeholder="Webhook URL" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} />
              <input placeholder="Secret" value={webhookSecret} onChange={(e) => setWebhookSecret(e.target.value)} />
              <button type="button" disabled={!canMutate} onClick={() => void onWebhook()}>
                Webhook
              </button>
              <button type="button" disabled={!canMutate} onClick={() => void onRotateKey()}>
                Rotacionar API key
              </button>
            </div>
          </>
        ) : null}
      </div>

      <table style={tableStyle}>
        <thead>
          <tr>
            <th style={thStyle}>Tipo</th>
            <th style={thStyle}>Codigo</th>
            <th style={thStyle}>Detalhe</th>
          </tr>
        </thead>
        <tbody>
          {tab === "catalog" &&
            methods.map((m) => (
              <tr key={m.id}>
                <td style={tdStyle}>method</td>
                <td style={tdStyle}>{m.code}</td>
                <td style={tdStyle}>{m.name}</td>
              </tr>
            ))}
          {tab === "providers" &&
            providers.map((p) => (
              <tr key={p.id}>
                <td style={tdStyle}>psp</td>
                <td style={tdStyle}>{p.code}</td>
                <td style={tdStyle}>
                  {p.name} · {p.provider_type}
                </td>
              </tr>
            ))}
          {tab === "ops" && (
            <>
              {devices.map((d) => (
                <tr key={d.device_hash}>
                  <td style={tdStyle}>device</td>
                  <td style={tdStyle}>{String(d.device_hash).slice(0, 16)}</td>
                  <td style={tdStyle}>{d.locker_id || "—"}</td>
                </tr>
              ))}
              {idem.map((x) => (
                <tr key={x.id}>
                  <td style={tdStyle}>idem</td>
                  <td style={tdStyle}>{x.id}</td>
                  <td style={tdStyle}>{x.status}</td>
                </tr>
              ))}
              {risk.map((x) => (
                <tr key={x.id}>
                  <td style={tdStyle}>risk</td>
                  <td style={tdStyle}>{x.id}</td>
                  <td style={tdStyle}>
                    {x.decision} · {x.score}
                  </td>
                </tr>
              ))}
            </>
          )}
        </tbody>
      </table>
    </div>
  );
}

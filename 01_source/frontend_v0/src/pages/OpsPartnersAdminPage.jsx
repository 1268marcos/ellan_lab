
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

const BASE = import.meta.env.VITE_PARTNER_ADMIN_BASE_URL || "/api/pa";
const API = `${BASE}/v1/partner-admin`;
const PAGE_VERSION = "ops/partners/admin v0.1";

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

export default function OpsPartnersAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [tab, setTab] = useState("ecommerce");
  const [ecItems, setEcItems] = useState([]);
  const [lgItems, setLgItems] = useState([]);
  const [form, setForm] = useState({ name: "", code: "" });
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
      const [ec, lg] = await Promise.all([
        fetch(`${API}/ecommerce-partners`, { headers }),
        fetch(`${API}/logistics-partners`, { headers }),
      ]);
      const ecJson = await ec.json().catch(() => ({}));
      const lgJson = await lg.json().catch(() => ({}));
      if (!ec.ok) throw new Error(parseError(ecJson));
      if (!lg.ok) throw new Error(parseError(lgJson));
      setEcItems(ecJson.partners || []);
      setLgItems(lgJson.partners || []);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
      setEcItems([]);
      setLgItems([]);
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

  const onCreate = async () => {
    if (!token || !canMutate) return;
    const path = tab === "ecommerce" ? "ecommerce-partners" : "logistics-partners";
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/${path}`, { method: "POST", headers, body: JSON.stringify(form) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Parceiro ${j.code} criado.`);
      setSelectedId(j.id);
      setPartnerType(tab === "ecommerce" ? "ECOMMERCE" : "LOGISTICS");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/${path}`));
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
            events: ["order.created", "order.updated"],
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
          <Link to="/ops/lockers/create" style={crossShortcutLinkStyle}>
            Criar lockers
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
          CRUD e-commerce / logística, webhook e API key — <code style={{ color: "#e2e8f0" }}>{API}</code> — role{" "}
          <code style={{ color: "#e2e8f0" }}>admin_operacao</code> para escrita.
        </p>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Tipo de parceiro</h3>
            <div style={{ display: "flex", gap: 8 }}>
              <button type="button" style={tabButtonStyle(tab === "ecommerce")} onClick={() => setTab("ecommerce")}>
                E-commerce
              </button>
              <button type="button" style={tabButtonStyle(tab === "logistics")} onClick={() => setTab("logistics")}>
                Logística
              </button>
            </div>
          </div>
          <div style={healthLocalFilterRowStyle}>
            <label style={healthLocalFilterFieldStyle}>
              name
              <input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                style={healthLocalFilterInputStyle}
              />
            </label>
            <label style={healthLocalFilterFieldStyle}>
              code
              <input
                value={form.code}
                onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))}
                style={healthLocalFilterInputStyle}
              />
            </label>
          </div>
          <div style={toolbarStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => void load()} disabled={loading || !token}>
              {loading ? "Atualizando..." : "Listar"}
            </button>
            {canMutate ? (
              <>
                <button type="button" style={buttonGhostStyle} onClick={() => void onSeed()} disabled={loading}>
                  Seed
                </button>
                <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreate()} disabled={loading || !form.name || !form.code}>
                  Criar {tab === "ecommerce" ? "e-commerce" : "logística"}
                </button>
              </>
            ) : null}
          </div>
        </section>

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
                {items.map((p) => (
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
            <button type="button" style={buttonGhostStyle} onClick={() => void onWebhook()} disabled={!canMutate || !selectedId || !webhookUrl}>
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

        {err ? <div style={criticalBannerStyle} role="alert">{err}</div> : null}
        {ok ? <p style={okBannerStyle}>{ok}</p> : null}
        {!token ? <p style={summary24hHintStyle}>Faca login com perfil admin_operacao.</p> : null}
        {token && !canMutate ? <p style={summary24hHintStyle}>Escrita exige admin_operacao.</p> : null}

        {(ecItems.length > 0 || lgItems.length > 0) ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>
                Parceiros (e-commerce: {ecItems.length}, logística: {lgItems.length})
              </h3>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["tipo", "code", "name", "ativo"].map((h) => (
                      <th key={h} style={thStyle}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ecItems.map((p) => (
                    <tr key={`ec-${p.id}`}>
                      <td style={tdStyle}>EC</td>
                      <td style={tdStyle}><code>{p.code}</code></td>
                      <td style={tdStyle}>{p.name}</td>
                      <td style={tdStyle}>{p.active ? "Y" : "N"}</td>
                    </tr>
                  ))}
                  {lgItems.map((p) => (
                    <tr key={`lg-${p.id}`}>
                      <td style={tdStyle}>LG</td>
                      <td style={tdStyle}><code>{p.code}</code></td>
                      <td style={tdStyle}>{p.name}</td>
                      <td style={tdStyle}>{p.active ? "Y" : "N"}</td>
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

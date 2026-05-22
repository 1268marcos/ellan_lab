
import React, { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import {
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

const BASE = import.meta.env.VITE_PARTNER_ADMIN_BASE_URL || "/api/pa";
const API = `${BASE}/v1/partner-admin`;
const PAGE_VERSION = "ops/tenants/admin v0.1";

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

export default function OpsTenantsAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [tab, setTab] = useState("tenants");
  const [tenants, setTenants] = useState([]);
  const [domains, setDomains] = useState([]);
  const [links, setLinks] = useState([]);
  const [ecPartners, setEcPartners] = useState([]);
  const [selectedTenant, setSelectedTenant] = useState("");
  const [tenantForm, setTenantForm] = useState({
    tenant_id: "",
    cnpj: "",
    razao_social: "",
    regime: "SIMPLES",
    crt: "1",
  });
  const [domainInput, setDomainInput] = useState("");
  const [linkPartnerId, setLinkPartnerId] = useState("");
  const [linkType, setLinkType] = useState("ECOMMERCE");
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

  const loadTenants = useCallback(async () => {
    const r = await fetch(`${API}/tenants`, { headers });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(parseError(j));
    setTenants(j.tenants || []);
    if (!selectedTenant && j.tenants?.length) setSelectedTenant(j.tenants[0].tenant_id);
  }, [headers, selectedTenant]);

  const loadAssociations = useCallback(
    async (tenantId) => {
      if (!tenantId) {
        setDomains([]);
        setLinks([]);
        return;
      }
      const [d, l] = await Promise.all([
        fetch(`${API}/tenants/${encodeURIComponent(tenantId)}/domains`, { headers }),
        fetch(`${API}/tenants/${encodeURIComponent(tenantId)}/partner-links`, { headers }),
      ]);
      const dj = await d.json().catch(() => ({}));
      const lj = await l.json().catch(() => ({}));
      if (!d.ok) throw new Error(parseError(dj));
      if (!l.ok) throw new Error(parseError(lj));
      setDomains(dj.domains || []);
      setLinks(lj.links || []);
    },
    [headers],
  );

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErr("");
    setOk("");
    try {
      const ec = await fetch(`${API}/ecommerce-partners`, { headers });
      const ecJson = await ec.json().catch(() => ({}));
      if (ec.ok) setEcPartners(ecJson.partners || []);
      await loadTenants();
      const tid = selectedTenant || "";
      if (tid) await loadAssociations(tid);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  }, [token, headers, loadTenants, loadAssociations, selectedTenant]);

  const onSeed = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
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

  const onCreateTenant = async (e) => {
    e.preventDefault();
    if (!canMutate) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/tenants`, {
        method: "POST",
        headers,
        body: JSON.stringify(tenantForm),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Tenant ${j.tenant_id} criado.`);
      setSelectedTenant(j.tenant_id);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onAddDomain = async () => {
    if (!selectedTenant || !domainInput) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/tenants/${encodeURIComponent(selectedTenant)}/domains`, {
        method: "POST",
        headers,
        body: JSON.stringify({ domain: domainInput, verified: false }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Dominio ${domainInput} adicionado.`);
      setDomainInput("");
      await loadAssociations(selectedTenant);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onAddLink = async () => {
    if (!selectedTenant || !linkPartnerId) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/tenants/${encodeURIComponent(selectedTenant)}/partner-links`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          partner_id: linkPartnerId,
          partner_type: linkType,
          is_default: true,
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Vinculo parceiro criado.");
      await loadAssociations(selectedTenant);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onTenantChange = async (tid) => {
    setSelectedTenant(tid);
    setLoading(true);
    try {
      await loadAssociations(tid);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={pageStyle}>
      <OpsPageTitleHeader
        title="OPS / Tenants"
        subtitle="tenant_fiscal_config, custom_domains e vinculos com parceiros."
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
          Parceiros
        </Link>
        <Link to="/ops/payment-gateway/admin" style={crossShortcutLinkStyle}>
          Payment Gateway
        </Link>
      </div>
      {err ? <p style={{ color: "#b91c1c" }}>{err}</p> : null}
      {ok ? <p style={okBannerStyle}>{ok}</p> : null}
      <p style={mutedTextStyle}>{loading ? "Processando…" : null}</p>

      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        {["tenants", "domains", "links"].map((t) => (
          <button key={t} type="button" style={tabButtonStyle(tab === t)} onClick={() => setTab(t)}>
            {t === "tenants" ? "Tenants" : t === "domains" ? "Dominios" : "Parceiros"}
          </button>
        ))}
      </div>

      <div style={cardStyle}>
        <select value={selectedTenant} onChange={(e) => void onTenantChange(e.target.value)}>
          <option value="">Tenant</option>
          {tenants.map((t) => (
            <option key={t.tenant_id} value={t.tenant_id}>
              {t.tenant_id} — {t.razao_social}
            </option>
          ))}
        </select>

        {tab === "tenants" ? (
          <form onSubmit={onCreateTenant} style={{ marginTop: 12, display: "grid", gap: 8 }}>
            <input
              placeholder="tenant_id"
              value={tenantForm.tenant_id}
              onChange={(e) => setTenantForm((f) => ({ ...f, tenant_id: e.target.value }))}
              required
            />
            <input
              placeholder="CNPJ"
              value={tenantForm.cnpj}
              onChange={(e) => setTenantForm((f) => ({ ...f, cnpj: e.target.value }))}
              required
            />
            <input
              placeholder="Razao social"
              value={tenantForm.razao_social}
              onChange={(e) => setTenantForm((f) => ({ ...f, razao_social: e.target.value }))}
              required
            />
            <button type="submit" disabled={!canMutate}>
              Criar tenant
            </button>
          </form>
        ) : null}

        {tab === "domains" ? (
          <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
            <input
              placeholder="dominio white-label"
              value={domainInput}
              onChange={(e) => setDomainInput(e.target.value)}
            />
            <button type="button" disabled={!canMutate || !selectedTenant} onClick={() => void onAddDomain()}>
              Adicionar dominio
            </button>
          </div>
        ) : null}

        {tab === "links" ? (
          <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
            <select value={linkType} onChange={(e) => setLinkType(e.target.value)}>
              <option value="ECOMMERCE">ECOMMERCE</option>
              <option value="LOGISTICS">LOGISTICS</option>
            </select>
            <select value={linkPartnerId} onChange={(e) => setLinkPartnerId(e.target.value)}>
              <option value="">Parceiro</option>
              {ecPartners.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.code}
                </option>
              ))}
            </select>
            <button type="button" disabled={!canMutate || !selectedTenant} onClick={() => void onAddLink()}>
              Vincular parceiro
            </button>
          </div>
        ) : null}
      </div>

      <table style={tableStyle}>
        <thead>
          <tr>
            <th style={thStyle}>Tipo</th>
            <th style={thStyle}>ID</th>
            <th style={thStyle}>Detalhe</th>
          </tr>
        </thead>
        <tbody>
          {tab === "tenants" &&
            tenants.map((t) => (
              <tr key={t.tenant_id}>
                <td style={tdStyle}>tenant</td>
                <td style={tdStyle}>{t.tenant_id}</td>
                <td style={tdStyle}>
                  {t.razao_social} · {t.cnpj} · {t.is_active ? "ativo" : "inativo"}
                </td>
              </tr>
            ))}
          {tab === "domains" &&
            domains.map((d) => (
              <tr key={d.id}>
                <td style={tdStyle}>domain</td>
                <td style={tdStyle}>{d.id}</td>
                <td style={tdStyle}>
                  {d.domain} · {d.verified ? "verificado" : "pendente"}
                </td>
              </tr>
            ))}
          {tab === "links" &&
            links.map((l) => (
              <tr key={l.id}>
                <td style={tdStyle}>{l.partner_type}</td>
                <td style={tdStyle}>{l.partner_id}</td>
                <td style={tdStyle}>{l.is_default ? "default" : ""}</td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}

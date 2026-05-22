
import React, { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import {
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
      const [tRes, ecRes] = await Promise.all([
        fetch(`${API}/tenants`, { headers }),
        fetch(`${API}/ecommerce-partners`, { headers }),
      ]);
      const tJson = await tRes.json().catch(() => ({}));
      const ecJson = await ecRes.json().catch(() => ({}));
      if (!tRes.ok) throw new Error(parseError(tJson));
      if (ecRes.ok) setEcPartners(ecJson.partners || []);
      const list = tJson.tenants || [];
      setTenants(list);
      const tid = selectedTenant || list[0]?.tenant_id || "";
      if (tid && tid !== selectedTenant) setSelectedTenant(tid);
      if (tid) await loadAssociations(tid);
      else {
        setDomains([]);
        setLinks([]);
      }
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
      setTenants([]);
      setDomains([]);
      setLinks([]);
    } finally {
      setLoading(false);
    }
  }, [token, headers, loadAssociations, selectedTenant]);

  const onSeed = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seed`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Seed aplicado (tenant demo, dominio e vinculo).");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seed`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateTenant = async (e) => {
    e.preventDefault();
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
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
      setErr(normalizeNetworkError(e, `${API}/tenants`));
    } finally {
      setLoading(false);
    }
  };

  const onAddDomain = async () => {
    if (!token || !canMutate || !selectedTenant || !domainInput) return;
    setLoading(true);
    setErr("");
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
      setErr(normalizeNetworkError(e, `${API}/tenants/.../domains`));
    } finally {
      setLoading(false);
    }
  };

  const onAddLink = async () => {
    if (!token || !canMutate || !selectedTenant || !linkPartnerId) return;
    setLoading(true);
    setErr("");
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
      setOk("Vinculo com parceiro criado.");
      await loadAssociations(selectedTenant);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/tenants/.../partner-links`));
    } finally {
      setLoading(false);
    }
  };

  const onTenantChange = async (tid) => {
    setSelectedTenant(tid);
    if (!tid) {
      setDomains([]);
      setLinks([]);
      return;
    }
    setLoading(true);
    setErr("");
    try {
      await loadAssociations(tid);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const tableRows =
    tab === "tenants"
      ? tenants.map((t) => ({
          key: `t-${t.tenant_id}`,
          tipo: "tenant",
          id: t.tenant_id,
          detalhe: `${t.razao_social} · ${t.cnpj} · regime ${t.regime || "—"} · ${t.is_active ? "ativo" : "inativo"}`,
        }))
      : tab === "domains"
        ? domains.map((d) => ({
            key: `d-${d.id}`,
            tipo: "domain",
            id: d.id,
            detalhe: `${d.domain} · ${d.verified ? "verificado" : "pendente"}`,
          }))
        : links.map((l) => ({
            key: `l-${l.id}`,
            tipo: l.partner_type,
            id: l.partner_id,
            detalhe: `${l.is_default ? "default" : "secundario"} · tenant ${selectedTenant}`,
          }));

  const listCount = tableRows.length;

  const listTitle =
    tab === "tenants"
      ? `Tenants fiscais (${tenants.length})`
      : tab === "domains"
        ? `Dominios white-label (${domains.length}) · tenant ${selectedTenant || "—"}`
        : `Vinculos parceiro (${links.length}) · tenant ${selectedTenant || "—"}`;

  return (
    <div style={pageStyle} data-testid="ops-tenants-admin-page">
      <section style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10, gap: 8 }}>
          <Link to="/ops/partners/admin" style={crossShortcutLinkStyle}>
            Parceiros
          </Link>
          <Link to="/ops/access/user-roles" style={crossShortcutLinkStyle}>
            user_roles
          </Link>
          <Link to="/ops/payment-gateway/admin" style={crossShortcutLinkStyle}>
            Payment Gateway
          </Link>
          <Link to="/ops/order-pickup/admin" style={crossShortcutLinkStyle}>
            Order Pickup
          </Link>
        </div>

        <OpsPageTitleHeader
          title="OPS — Tenants (white label)"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          tenant_fiscal_config, custom_domains e tenant_partner_links — <code style={{ color: "#e2e8f0" }}>{API}</code> — role{" "}
          <code style={{ color: "#e2e8f0" }}>admin_operacao</code> para escrita.
        </p>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Tenant em foco</h3>
          </div>
          <div style={healthLocalFilterRowStyle}>
            <label style={healthLocalFilterFieldStyle}>
              tenant_id
              <select
                value={selectedTenant}
                onChange={(e) => void onTenantChange(e.target.value)}
                style={healthLocalFilterInputStyle}
              >
                <option value="">— selecione —</option>
                {tenants.map((t) => (
                  <option key={t.tenant_id} value={t.tenant_id}>
                    {t.tenant_id} — {t.razao_social}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </section>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Área de cadastro</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button type="button" style={tabButtonStyle(tab === "tenants")} onClick={() => setTab("tenants")}>
                Tenants
              </button>
              <button type="button" style={tabButtonStyle(tab === "domains")} onClick={() => setTab("domains")}>
                Domínios
              </button>
              <button type="button" style={tabButtonStyle(tab === "links")} onClick={() => setTab("links")}>
                Vínculos
              </button>
            </div>
          </div>

          {tab === "tenants" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                tenant_id
                <input
                  value={tenantForm.tenant_id}
                  onChange={(e) => setTenantForm((f) => ({ ...f, tenant_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="tenant-demo"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                cnpj
                <input
                  value={tenantForm.cnpj}
                  onChange={(e) => setTenantForm((f) => ({ ...f, cnpj: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                razao_social
                <input
                  value={tenantForm.razao_social}
                  onChange={(e) => setTenantForm((f) => ({ ...f, razao_social: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                regime
                <select
                  value={tenantForm.regime}
                  onChange={(e) => setTenantForm((f) => ({ ...f, regime: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="SIMPLES">SIMPLES</option>
                  <option value="NORMAL">NORMAL</option>
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                crt
                <input
                  value={tenantForm.crt}
                  onChange={(e) => setTenantForm((f) => ({ ...f, crt: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
            </div>
          ) : null}

          {tab === "domains" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                domain
                <input
                  value={domainInput}
                  onChange={(e) => setDomainInput(e.target.value)}
                  style={healthLocalFilterInputStyle}
                  placeholder="app.parceiro.example"
                />
              </label>
            </div>
          ) : null}

          {tab === "links" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                partner_type
                <select value={linkType} onChange={(e) => setLinkType(e.target.value)} style={healthLocalFilterInputStyle}>
                  <option value="ECOMMERCE">ECOMMERCE</option>
                  <option value="LOGISTICS">LOGISTICS</option>
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                partner_id
                <select value={linkPartnerId} onChange={(e) => setLinkPartnerId(e.target.value)} style={healthLocalFilterInputStyle}>
                  <option value="">— selecione —</option>
                  {ecPartners.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.code}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ) : null}

          {tab === "domains" && !selectedTenant ? (
            <p style={summary24hHintStyle}>Selecione um tenant para gerenciar dominios.</p>
          ) : null}
          {tab === "links" && !selectedTenant ? (
            <p style={summary24hHintStyle}>Selecione um tenant para vincular parceiros.</p>
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
                {tab === "tenants" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={(e) => void onCreateTenant(e)}
                    disabled={
                      loading || !tenantForm.tenant_id || !tenantForm.cnpj || !tenantForm.razao_social
                    }
                  >
                    Criar tenant
                  </button>
                ) : null}
                {tab === "domains" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onAddDomain()}
                    disabled={loading || !selectedTenant || !domainInput}
                  >
                    Adicionar dominio
                  </button>
                ) : null}
                {tab === "links" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onAddLink()}
                    disabled={loading || !selectedTenant || !linkPartnerId}
                  >
                    Vincular parceiro
                  </button>
                ) : null}
              </>
            ) : null}
          </div>

        </section>

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
        ) : token && !loading ? (
          <p style={summary24hHintStyle}>Nenhum registro. Use Listar ou Seed (admin_operacao).</p>
        ) : null}
      </section>
    </div>
  );
}


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

const BASE = import.meta.env.VITE_PARTNER_ADMIN_BASE_URL || "/api/pa";
const API = `${BASE}/v1/partner-admin`;
const SEC = `${API}/security-admin`;
const VAL = `${SEC}/value`;
const PAGE_VERSION = "ops/access/security-admin v0.2-pro";
const ROLES = ["admin_operacao", "suporte", "auditoria", "usuario_comum", "partner_api", "carrier_ops"];

const TABS = [
  ["overview", "Visao geral"],
  ["domains", "Dominios OPS"],
  ["ecosystem", "Mapa ecossistema"],
  ["locker-players", "Players locker mundial"],
  ["intelligence", "Inteligencia OPS"],
  ["taxonomy", "Taxonomia mundial"],
  ["relations", "Relacoes player"],
  ["access-review", "Revisao acesso"],
  ["alerts", "Alertas"],
  ["compliance", "Compliance"],
  ["templates", "Templates onboarding"],
  ["matrix", "Matriz acesso"],
  ["users", "Usuarios"],
  ["user-360", "Usuario 360"],
  ["roles", "Papeis"],
  ["role-catalog", "Catalogo roles"],
  ["permissions", "Permissoes"],
  ["grants", "Grants cross-domain"],
  ["webhooks", "Webhooks"],
  ["deliveries", "Entregas WH"],
  ["api-keys", "API keys"],
  ["sessions", "Sessoes"],
  ["identity", "Identity / SSO"],
  ["policy", "Policy snapshots"],
  ["audit", "Auditoria"],
  ["cross-domain", "Links legado"],
];

function parseError(payload, fallback = "Falha na API security-admin.") {
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

export default function OpsUsersSecurityAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get("tab") || "overview";
  const [tab, setTab] = useState(TABS.some(([k]) => k === initialTab) ? initialTab : "overview");
  const [summary, setSummary] = useState(null);
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [groups, setGroups] = useState([]);
  const [perms, setPerms] = useState([]);
  const [memberships, setMemberships] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [apiKeys, setApiKeys] = useState([]);
  const [audit, setAudit] = useState([]);
  const [links, setLinks] = useState([]);
  const [domainCatalog, setDomainCatalog] = useState([]);
  const [domainHealth, setDomainHealth] = useState([]);
  const [roleCatalog, setRoleCatalog] = useState([]);
  const [grants, setGrants] = useState([]);
  const [ecosystem, setEcosystem] = useState(null);
  const [lockerPlayers, setLockerPlayers] = useState([]);
  const [playerProfile, setPlayerProfile] = useState(null);
  const [playerCode, setPlayerCode] = useState("INPOST");
  const [userPlayerAccess, setUserPlayerAccess] = useState([]);
  const [taxonomy, setTaxonomy] = useState(null);
  const [segments, setSegments] = useState([]);
  const [relations, setRelations] = useState([]);
  const [intel, setIntel] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [compliance, setCompliance] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [matrix, setMatrix] = useState(null);
  const [user360, setUser360] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [deliveries, setDeliveries] = useState([]);
  const [idps, setIdps] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [user360Id, setUser360Id] = useState("usr-admin-ops");
  const [userForm, setUserForm] = useState({ full_name: "", email: "", phone: "" });
  const [roleForm, setRoleForm] = useState({ user_id: "", role: "suporte", scope_type: "GLOBAL" });
  const [whUrl, setWhUrl] = useState("");
  const [apiKeyUser, setApiKeyUser] = useState("");
  const [lastSecret, setLastSecret] = useState("");
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

  const setTabUrl = (id) => {
    setTab(id);
    const next = new URLSearchParams(searchParams);
    next.set("tab", id);
    setSearchParams(next, { replace: true });
  };

  const loadCore = useCallback(async () => {
    const [u, r] = await Promise.all([
      fetch(`${API}/users`, { headers }),
      fetch(`${API}/user-roles?active_only=false`, { headers }),
    ]);
    const uj = await u.json().catch(() => ({}));
    const rj = await r.json().catch(() => ({}));
    if (!u.ok) throw new Error(parseError(uj));
    if (!rj.ok) throw new Error(parseError(rj));
    setUsers(uj.users || []);
    setRoles(rj.roles || []);
  }, [headers]);

  const loadTab = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErr("");
    setOk("");
    try {
      if (tab === "overview") {
        const s = await fetch(`${SEC}/summary`, { headers });
        const sj = await s.json().catch(() => ({}));
        if (!s.ok) throw new Error(parseError(sj));
        setSummary(sj);
        await loadCore();
        return;
      }
      if (tab === "users" || tab === "roles") {
        await loadCore();
        return;
      }
      if (tab === "permissions") {
        const [g, p, m] = await Promise.all([
          fetch(`${SEC}/permission-groups`, { headers }),
          fetch(`${SEC}/permissions`, { headers }),
          fetch(`${SEC}/permission-memberships`, { headers }),
        ]);
        const gj = await g.json().catch(() => ({}));
        const pj = await p.json().catch(() => ({}));
        const mj = await m.json().catch(() => ({}));
        if (!g.ok) throw new Error(parseError(gj));
        setGroups(gj.items || []);
        setPerms(pj.items || []);
        setMemberships(mj.items || []);
        await loadCore();
        return;
      }
      if (tab === "webhooks") {
        const w = await fetch(`${SEC}/webhook-endpoints`, { headers });
        const wj = await w.json().catch(() => ({}));
        if (!w.ok) throw new Error(parseError(wj));
        setWebhooks(wj.items || []);
        return;
      }
      if (tab === "api-keys") {
        const k = await fetch(`${SEC}/api-keys`, { headers });
        const kj = await k.json().catch(() => ({}));
        if (!k.ok) throw new Error(parseError(kj));
        setApiKeys(kj.items || []);
        await loadCore();
        return;
      }
      if (tab === "audit") {
        const a = await fetch(`${SEC}/audit-logs?limit=80`, { headers });
        const aj = await a.json().catch(() => ({}));
        if (!a.ok) throw new Error(parseError(aj));
        setAudit(aj.items || []);
        return;
      }
      if (tab === "domains") {
        const [c, h] = await Promise.all([
          fetch(`${SEC}/domain-catalog`, { headers }),
          fetch(`${SEC}/cross-domain/health`, { headers }),
        ]);
        const cj = await c.json().catch(() => ({}));
        const hj = await h.json().catch(() => ({}));
        if (!c.ok) throw new Error(parseError(cj));
        setDomainCatalog(cj.items || []);
        setDomainHealth(hj.items || []);
        return;
      }
      if (tab === "ecosystem") {
        const e = await fetch(`${SEC}/cross-domain/ecosystem-map`, { headers });
        const ej = await e.json().catch(() => ({}));
        if (!e.ok) throw new Error(parseError(ej));
        setEcosystem(ej);
        return;
      }
      if (tab === "intelligence") {
        const i = await fetch(`${VAL}/intelligence`, { headers });
        const ij = await i.json().catch(() => ({}));
        if (!i.ok) throw new Error(parseError(ij));
        setIntel(ij);
        return;
      }
      if (tab === "access-review") {
        const c = await fetch(`${VAL}/access-reviews`, { headers });
        const cj = await c.json().catch(() => ({}));
        if (!c.ok) throw new Error(parseError(cj));
        setCampaigns(cj.items || []);
        return;
      }
      if (tab === "alerts") {
        const a = await fetch(`${VAL}/alerts`, { headers });
        const aj = await a.json().catch(() => ({}));
        if (!a.ok) throw new Error(parseError(aj));
        setAlerts(aj.items || []);
        return;
      }
      if (tab === "compliance") {
        const c = await fetch(`${VAL}/compliance`, { headers });
        const cj = await c.json().catch(() => ({}));
        if (!c.ok) throw new Error(parseError(cj));
        setCompliance(cj);
        return;
      }
      if (tab === "templates") {
        const t = await fetch(`${VAL}/role-templates`, { headers });
        const tj = await t.json().catch(() => ({}));
        if (!t.ok) throw new Error(parseError(tj));
        setTemplates(tj.items || []);
        return;
      }
      if (tab === "matrix") {
        const m = await fetch(`${VAL}/access-matrix`, { headers });
        const mj = await m.json().catch(() => ({}));
        if (!m.ok) throw new Error(parseError(mj));
        setMatrix(mj);
        return;
      }
      if (tab === "taxonomy") {
        const [t, s] = await Promise.all([
          fetch(`${SEC}/ecosystem-taxonomy/summary`, { headers }),
          fetch(`${SEC}/player-segments`, { headers }),
        ]);
        const tj = await t.json().catch(() => ({}));
        const sj = await s.json().catch(() => ({}));
        if (!t.ok) throw new Error(parseError(tj));
        setTaxonomy(tj);
        setSegments(sj.items || []);
        return;
      }
      if (tab === "relations") {
        const rel = await fetch(`${SEC}/player-relations?limit=80`, { headers });
        const rj = await rel.json().catch(() => ({}));
        if (!rel.ok) throw new Error(parseError(rj));
        setRelations(rj.items || []);
        return;
      }
      if (tab === "locker-players") {
        const [lp, upa] = await Promise.all([
          fetch(`${SEC}/locker-players/priority`, { headers }),
          fetch(`${SEC}/user-player-access`, { headers }),
        ]);
        const lpj = await lp.json().catch(() => ({}));
        const upaj = await upa.json().catch(() => ({}));
        if (!lp.ok) throw new Error(parseError(lpj));
        setLockerPlayers(lpj.items || []);
        setUserPlayerAccess(upaj.items || []);
        const prof = await fetch(`${SEC}/locker-players/${encodeURIComponent(playerCode)}/security-profile`, { headers });
        const prj = await prof.json().catch(() => ({}));
        if (prof.ok) setPlayerProfile(prj);
        return;
      }
      if (tab === "user-360") {
        await loadCore();
        const u = await fetch(`${SEC}/users/${encodeURIComponent(user360Id)}/360`, { headers });
        const uj = await u.json().catch(() => ({}));
        if (!u.ok) throw new Error(parseError(uj));
        setUser360(uj);
        return;
      }
      if (tab === "role-catalog") {
        const rc = await fetch(`${SEC}/role-catalog`, { headers });
        const rcj = await rc.json().catch(() => ({}));
        if (!rc.ok) throw new Error(parseError(rcj));
        setRoleCatalog(rcj.items || []);
        return;
      }
      if (tab === "grants") {
        const g = await fetch(`${SEC}/cross-domain-grants`, { headers });
        const gj = await g.json().catch(() => ({}));
        if (!g.ok) throw new Error(parseError(gj));
        setGrants(gj.items || []);
        await loadCore();
        return;
      }
      if (tab === "sessions") {
        const s = await fetch(`${SEC}/sessions`, { headers });
        const sj = await s.json().catch(() => ({}));
        if (!s.ok) throw new Error(parseError(sj));
        setSessions(sj.items || []);
        return;
      }
      if (tab === "deliveries") {
        const d = await fetch(`${SEC}/webhook-deliveries`, { headers });
        const dj = await d.json().catch(() => ({}));
        if (!d.ok) throw new Error(parseError(dj));
        setDeliveries(dj.items || []);
        return;
      }
      if (tab === "identity") {
        const i = await fetch(`${SEC}/identity-providers`, { headers });
        const ij = await i.json().catch(() => ({}));
        if (!i.ok) throw new Error(parseError(ij));
        setIdps(ij.items || []);
        return;
      }
      if (tab === "policy") {
        const p = await fetch(`${SEC}/policy-snapshots`, { headers });
        const pj = await p.json().catch(() => ({}));
        if (!p.ok) throw new Error(parseError(pj));
        setPolicies(pj.items || []);
        return;
      }
      if (tab === "cross-domain") {
        const l = await fetch(`${SEC}/domain-links`, { headers });
        const lj = await l.json().catch(() => ({}));
        if (!l.ok) throw new Error(parseError(lj));
        setLinks(lj.items || []);
        await loadCore();
      }
    } catch (e) {
      setErr(normalizeNetworkError(e, SEC));
    } finally {
      setLoading(false);
    }
  }, [token, headers, tab, loadCore]);

  useEffect(() => {
    void loadTab();
  }, [loadTab]);

  const onSeed = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    try {
      const r = await fetch(`${SEC}/seed`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Seed security aplicado.");
      await loadTab();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${SEC}/seed`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateUser = async () => {
    if (!canMutate || !userForm.email) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/users`, { method: "POST", headers, body: JSON.stringify({ ...userForm, is_active: true }) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Usuario criado: ${j.id}`);
      setUserForm({ full_name: "", email: "", phone: "" });
      await loadTab();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/users`));
    } finally {
      setLoading(false);
    }
  };

  const onGrantRole = async () => {
    if (!canMutate || !roleForm.user_id) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/user-roles`, { method: "POST", headers, body: JSON.stringify(roleForm) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Role concedida.");
      await loadTab();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/user-roles`));
    } finally {
      setLoading(false);
    }
  };

  const onRevokeRole = async (roleId) => {
    if (!canMutate) return;
    const r = await fetch(`${API}/user-roles/${encodeURIComponent(roleId)}/revoke`, { method: "POST", headers });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) setErr(parseError(j));
    else {
      setOk("Role revogada.");
      await loadTab();
    }
  };

  const onCreateWebhook = async () => {
    if (!canMutate || !whUrl) return;
    setLoading(true);
    try {
      const r = await fetch(`${SEC}/webhook-endpoints`, {
        method: "POST",
        headers,
        body: JSON.stringify({ url: whUrl, events: ["user.created", "role.granted"] }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Webhook criado.");
      setWhUrl("");
      await loadTab();
    } catch (e) {
      setErr(normalizeNetworkError(e, SEC));
    } finally {
      setLoading(false);
    }
  };

  const onRotateWebhook = async (id) => {
    if (!canMutate) return;
    const r = await fetch(`${SEC}/webhook-endpoints/${encodeURIComponent(id)}/rotate-secret`, { method: "POST", headers });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) setErr(parseError(j));
    else {
      setLastSecret(j.webhook_secret);
      setOk("Secret rotacionado (copie agora).");
    }
  };

  const onRotateApiKey = async () => {
    if (!canMutate || !apiKeyUser) return;
    const r = await fetch(`${SEC}/api-keys/rotate`, {
      method: "POST",
      headers,
      body: JSON.stringify({ user_id: apiKeyUser, scopes: ["ops:read", "ops:write"] }),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) setErr(parseError(j));
    else {
      setLastApiKey(j.api_key);
      setOk("API key rotacionada.");
      await loadTab();
    }
  };

  const renderTable = (rows, cols, keyFn) => (
    <div style={{ overflowX: "auto" }}>
      <table style={tableStyle}>
        <thead>
          <tr>{cols.map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={keyFn(row)}>{cols.map((c) => <td key={c} style={tdStyle}>{String(row[c] ?? "—")}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10, gap: 8 }}>
          <Link to="/ops/access/user-roles" style={crossShortcutLinkStyle}>user_roles (legado)</Link>
          <Link to="/ops/partners/admin" style={crossShortcutLinkStyle}>Parceiros</Link>
          <Link to="/ops/payment-gateway/admin" style={crossShortcutLinkStyle}>Payment Gateway</Link>
          <Link to="/ops/marketplace/admin" style={crossShortcutLinkStyle}>Marketplace</Link>
          <Link to="/ops/hardware/admin" style={crossShortcutLinkStyle}>Hardware</Link>
        </div>

        <OpsPageTitleHeader
          title="OPS — Users & Roles & Security"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Usuarios, papeis, grupos de permissao, webhooks, API keys e auditoria — <code style={{ color: "#e2e8f0" }}>{SEC}</code>
        </p>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
          {TABS.map(([id, label]) => (
            <button key={id} type="button" style={tabButtonStyle(tab === id)} onClick={() => setTabUrl(id)}>
              {label}
            </button>
          ))}
        </div>

        <div style={toolbarStyle}>
          <button type="button" style={buttonGhostStyle} onClick={() => void loadTab()} disabled={loading || !token}>
            {loading ? "..." : "Atualizar"}
          </button>
          {canMutate ? (
            <button type="button" style={buttonPrimaryStyle} onClick={() => void onSeed()} disabled={loading}>
              Seed security
            </button>
          ) : null}
        </div>

        {err ? <div style={criticalBannerStyle} role="alert">{err}</div> : null}
        {ok ? <p style={okBannerStyle}>{ok}</p> : null}
        {lastSecret ? <p style={apiKeyBannerStyle}>Webhook secret: <code>{lastSecret}</code></p> : null}
        {lastApiKey ? <p style={apiKeyBannerStyle}>API key: <code>{lastApiKey}</code></p> : null}

        {tab === "overview" && summary ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}><h3 style={{ margin: 0, fontSize: 14 }}>Resumo mundial</h3></div>
            <p style={summary24hHintStyle}>
              {summary.users} usuarios · {summary.active_roles} roles · {summary.locker_players ?? 0} players locker ·{" "}
              {summary.user_player_access ?? 0} acessos player · {summary.cross_domain_grants ?? 0} grants ·{" "}
              {summary.domains_reachable ?? 0}/{summary.domains_total ?? 0} dominios online
            </p>
            <p style={summary24hHintStyle}>
              Prioridade: InPost, DHL, DPD, Magalu, Mercado Livre, Amazon, Correios, CTT, Worten, El Corte Ingles
            </p>
          </section>
        ) : null}

        {tab === "intelligence" && intel ? (
          <section style={opsSanityCardStyle}>
            <p style={summary24hHintStyle}>
              Postura: <strong>{intel.overall_posture}</strong> · risco médio {intel.average_user_risk} · {intel.open_alerts} alertas · {intel.pending_reviews} revisões pendentes
            </p>
            <ul style={{ margin: 0, paddingLeft: 18, color: "#94a3b8", fontSize: 13 }}>
              {(intel.recommendations || []).map((rec) => <li key={rec}>{rec}</li>)}
            </ul>
          </section>
        ) : null}

        {tab === "alerts" && alerts.length ? renderTable(
          alerts.map((a) => ({ title: a.title, severity: a.severity, status: a.status, entity: a.entity_id || "—" })),
          ["title", "severity", "status", "entity"],
          (a) => a.title,
        ) : null}

        {tab === "compliance" && compliance ? (
          <p style={summary24hHintStyle}>Cobertura compliance: {compliance.coverage_pct}% · {compliance.total} controles</p>
        ) : null}

        {tab === "templates" && templates.length ? renderTable(
          templates.map((t) => ({ code: t.code, name: t.name, segment: t.target_segment || "—", roles: (t.roles || []).join(",") })),
          ["code", "name", "segment", "roles"],
          (t) => t.code,
        ) : null}

        {tab === "access-review" && campaigns.length ? renderTable(
          campaigns.map((c) => ({ name: c.name, status: c.status, pending: c.pending_items, due: c.due_at })),
          ["name", "status", "pending", "due"],
          (c) => c.id,
        ) : null}

        {tab === "matrix" && matrix ? (
          <p style={summary24hHintStyle}>{matrix.cells?.length ?? 0} células usuário×domínio (grants ativos)</p>
        ) : null}

        {tab === "taxonomy" && taxonomy ? (
          <section style={opsSanityCardStyle}>
            <p style={summary24hHintStyle}>
              {taxonomy.total_players} players · {taxonomy.total_relations} relacoes · {taxonomy.total_integrations} integracoes
            </p>
            <p style={summary24hHintStyle}>
              Food: {(taxonomy.food_delivery_players || []).slice(0, 8).join(", ")}… · PUDO: {(taxonomy.collection_point_players || []).slice(0, 5).join(", ")}…
            </p>
            {segments.length ? renderTable(
              segments.map((s) => ({ code: s.code, label: s.label, players: s.player_count, domain: s.primary_domain })),
              ["code", "label", "players", "domain"],
              (s) => s.code,
            ) : null}
          </section>
        ) : null}

        {tab === "relations" && relations.length ? renderTable(
          relations.slice(0, 50).map((r) => ({ from: r.from_player_code, to: r.to_player_code, type: r.relation_type, strength: r.strength })),
          ["from", "to", "type", "strength"],
          (r) => r.from + r.to + r.type,
        ) : null}

        {tab === "locker-players" ? (
          <section style={opsSanityCardStyle}>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>player
                <select value={playerCode} onChange={(e) => setPlayerCode(e.target.value)} style={healthLocalFilterInputStyle}>
                  {lockerPlayers.map((p) => (
                    <option key={p.player_code} value={p.player_code}>{p.name}</option>
                  ))}
                </select>
              </label>
              <button type="button" style={buttonGhostStyle} onClick={() => void loadTab()}>Perfil seguranca</button>
            </div>
            {lockerPlayers.length ? renderTable(
              lockerPlayers.map((p) => ({
                code: p.player_code,
                name: p.name,
                segment: p.segment,
                domain: p.primary_domain,
                tier: p.global_tier,
                regions: (p.regions || []).join(","),
              })),
              ["code", "name", "segment", "domain", "tier", "regions"],
              (p) => p.code,
            ) : null}
            {playerProfile?.player ? (
              <p style={summary24hHintStyle}>
                {playerProfile.player.name}: dominios {playerProfile.player.related_domains?.join(", ")} · grants {playerProfile.suggested_grants?.length ?? 0}
              </p>
            ) : null}
            {userPlayerAccess.length ? renderTable(
              userPlayerAccess.slice(0, 30).map((a) => ({ user: a.user_id, player: a.player_code, role: a.access_role })),
              ["user", "player", "role"],
              (a) => a.user + a.player,
            ) : null}
          </section>
        ) : null}

        {tab === "domains" ? (
          <>
            {domainHealth.length ? renderTable(domainHealth.map((d) => ({ domain: d.domain, label: d.label, ok: d.reachable ? "online" : "offline" })), ["domain", "label", "ok"], (d) => d.domain) : null}
            {domainCatalog.length ? renderTable(domainCatalog.map((d) => ({ code: d.code, label: d.label, route: d.admin_route || "—" })), ["code", "label", "route"], (d) => d.code) : null}
          </>
        ) : null}

        {tab === "ecosystem" && ecosystem ? (
          <p style={summary24hHintStyle}>
            {ecosystem.entities?.length ?? 0} entidades · {ecosystem.remote_entities ?? 0} remotas (partner/marketplace)
          </p>
        ) : null}
        {tab === "ecosystem" && ecosystem?.entities?.length ? renderTable(
          ecosystem.entities.slice(0, 40).map((e) => ({ domain: e.domain, type: e.entity_type, id: e.entity_id, label: e.label, src: e.source })),
          ["domain", "type", "id", "label", "src"],
          (e) => e.domain + e.id,
        ) : null}

        {tab === "user-360" ? (
          <section style={opsSanityCardStyle}>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>user_id
                <select value={user360Id} onChange={(e) => setUser360Id(e.target.value)} style={healthLocalFilterInputStyle}>
                  {users.map((u) => <option key={u.id} value={u.id}>{u.email}</option>)}
                </select>
              </label>
              <button type="button" style={buttonGhostStyle} onClick={() => void loadTab()}>Carregar 360</button>
            </div>
            {user360 ? (
              <p style={summary24hHintStyle}>
                {user360.full_name} · roles: {(user360.roles || []).join(", ")} · grupos: {(user360.permission_groups || []).join(", ")} · sessoes: {user360.active_sessions}
              </p>
            ) : null}
          </section>
        ) : null}

        {tab === "role-catalog" && roleCatalog.length ? renderTable(roleCatalog.map((r) => ({ code: r.code, label: r.label, scope: r.default_scope_type })), ["code", "label", "scope"], (r) => r.code) : null}

        {tab === "grants" && grants.length ? renderTable(grants.map((g) => ({ user: g.user_id, domain: g.domain_code, entity: g.entity_id, perm: g.permission_key })), ["user", "domain", "entity", "perm"], (g) => g.id) : null}

        {tab === "sessions" && sessions.length ? renderTable(sessions.map((s) => ({ user: s.user_id, method: s.auth_method, ip: s.ip_address || "—", exp: s.expires_at })), ["user", "method", "ip", "exp"], (s) => s.id) : null}

        {tab === "deliveries" && deliveries.length ? renderTable(deliveries.map((d) => ({ event: d.event_name, status: d.status, attempts: d.attempt_count })), ["event", "status", "attempts"], (d) => d.id) : null}

        {tab === "identity" && idps.length ? renderTable(idps.map((i) => ({ code: i.code, name: i.name, type: i.provider_type, active: i.is_active ? "Y" : "N" })), ["code", "name", "type", "active"], (i) => i.code) : null}

        {tab === "policy" && policies.length ? renderTable(policies.map((p) => ({ version: p.version_label, kind: p.policy_kind, groups: p.groups_count, perms: p.permissions_count })), ["version", "kind", "groups", "perms"], (p) => p.id) : null}

        {tab === "users" ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}><h3 style={{ margin: 0, fontSize: 14 }}>Novo usuario</h3></div>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>nome<input value={userForm.full_name} onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })} style={healthLocalFilterInputStyle} /></label>
              <label style={healthLocalFilterFieldStyle}>email<input value={userForm.email} onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} style={healthLocalFilterInputStyle} /></label>
              {canMutate ? <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreateUser()}>Criar</button> : null}
            </div>
            {users.length ? renderTable(users, ["id", "full_name", "email", "is_active"], (u) => u.id) : <p style={summary24hHintStyle}>Sem usuarios.</p>}
          </section>
        ) : null}

        {tab === "roles" ? (
          <section style={opsSanityCardStyle}>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>user
                <select value={roleForm.user_id} onChange={(e) => setRoleForm({ ...roleForm, user_id: e.target.value })} style={healthLocalFilterInputStyle}>
                  <option value="">—</option>
                  {users.map((u) => <option key={u.id} value={u.id}>{u.email}</option>)}
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>role
                <select value={roleForm.role} onChange={(e) => setRoleForm({ ...roleForm, role: e.target.value })} style={healthLocalFilterInputStyle}>
                  {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
              </label>
              {canMutate ? <button type="button" style={buttonPrimaryStyle} onClick={() => void onGrantRole()}>Conceder</button> : null}
            </div>
            {roles.length ? (
              <table style={tableStyle}>
                <thead><tr>{["user_id", "role", "scope_type", "ativa", ""].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
                <tbody>
                  {roles.map((r) => (
                    <tr key={r.id}>
                      <td style={tdStyle}><code>{r.user_id}</code></td>
                      <td style={tdStyle}>{r.role}</td>
                      <td style={tdStyle}>{r.scope_type}</td>
                      <td style={tdStyle}>{r.is_active && !r.revoked_at ? "Y" : "N"}</td>
                      <td style={tdStyle}>{canMutate && r.is_active && !r.revoked_at ? <button type="button" style={buttonGhostStyle} onClick={() => void onRevokeRole(r.id)}>Revogar</button> : null}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : null}
          </section>
        ) : null}

        {tab === "permissions" ? (
          <>
            {groups.length ? renderTable(groups.map((g) => ({ id: g.id, name: g.name, system: g.is_system ? "Y" : "N" })), ["id", "name", "system"], (g) => g.id) : null}
            {perms.length ? renderTable(perms.map((p) => ({ group: p.group_id, object: p.object_key })), ["group", "object"], (p) => p.group + p.object) : null}
            {memberships.length ? renderTable(memberships.map((m) => ({ user: m.user_id, group: m.group_id, mgr: m.is_group_manager ? "Y" : "N" })), ["user", "group", "mgr"], (m) => m.user + m.group) : null}
          </>
        ) : null}

        {tab === "webhooks" ? (
          <section style={opsSanityCardStyle}>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>URL<input value={whUrl} onChange={(e) => setWhUrl(e.target.value)} style={healthLocalFilterInputStyle} /></label>
              {canMutate ? <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreateWebhook()}>Criar webhook</button> : null}
            </div>
            {webhooks.length ? (
              <table style={tableStyle}>
                <thead><tr>{["url", "events", "active", ""].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
                <tbody>
                  {webhooks.map((w) => (
                    <tr key={w.id}>
                      <td style={tdStyle}>{w.url}</td>
                      <td style={tdStyle}>{(w.events || []).join(", ")}</td>
                      <td style={tdStyle}>{w.active ? "Y" : "N"}</td>
                      <td style={tdStyle}>{canMutate ? <button type="button" style={buttonGhostStyle} onClick={() => void onRotateWebhook(w.id)}>Rotate secret</button> : null}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p style={summary24hHintStyle}>Sem webhooks.</p>}
          </section>
        ) : null}

        {tab === "api-keys" ? (
          <section style={opsSanityCardStyle}>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>user
                <select value={apiKeyUser} onChange={(e) => setApiKeyUser(e.target.value)} style={healthLocalFilterInputStyle}>
                  <option value="">—</option>
                  {users.map((u) => <option key={u.id} value={u.id}>{u.email}</option>)}
                </select>
              </label>
              {canMutate ? <button type="button" style={buttonPrimaryStyle} onClick={() => void onRotateApiKey()}>Rotacionar API key</button> : null}
            </div>
            {apiKeys.length ? renderTable(apiKeys.map((k) => ({ prefix: k.key_prefix, user: k.user_id, label: k.label || "—", revoked: k.revoked_at ? "Y" : "N" })), ["prefix", "user", "label", "revoked"], (k) => k.prefix) : null}
          </section>
        ) : null}

        {tab === "audit" && audit.length ? renderTable(audit.map((a) => ({ action: a.action, target: `${a.target_type}/${a.target_id}`, actor: a.actor_id || "—", at: a.occurred_at })), ["action", "target", "actor", "at"], (a) => a.action + a.at) : null}

        {tab === "cross-domain" && links.length ? renderTable(links.map((l) => ({ user: l.user_id, domain: l.domain, entity: `${l.entity_type}/${l.entity_id}`, rel: l.relation })), ["user", "domain", "entity", "rel"], (l) => l.user + l.entity) : null}
      </section>
    </div>
  );
}

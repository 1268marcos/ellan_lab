
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
  tableStyle,
  tdStyle,
  thStyle,
  toolbarStyle,
} from "../styles/opsShellStyles";

const BASE = import.meta.env.VITE_PARTNER_ADMIN_BASE_URL || "/api/pa";
const API = `${BASE}/v1/partner-admin`;
const PAGE_VERSION = "ops/access/user-roles v0.1";
const ROLES = ["admin_operacao", "suporte", "auditoria"];

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

export default function OpsUserRolesPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [userId, setUserId] = useState("");
  const [role, setRole] = useState("admin_operacao");
  const [scopeType, setScopeType] = useState("GLOBAL");
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
      const [u, r] = await Promise.all([
        fetch(`${API}/users`, { headers }),
        fetch(`${API}/user-roles?active_only=false`, { headers }),
      ]);
      const uJson = await u.json().catch(() => ({}));
      const rJson = await r.json().catch(() => ({}));
      if (!u.ok) throw new Error(parseError(uJson));
      if (!r.ok) throw new Error(parseError(rJson));
      setUsers(uJson.users || []);
      setRoles(rJson.roles || []);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
      setUsers([]);
      setRoles([]);
    } finally {
      setLoading(false);
    }
  }, [token, headers]);

  const onGrant = async () => {
    if (!token || !canMutate || !userId) return;
    setLoading(true);
    setErr("");
    try {
      const res = await fetch(`${API}/user-roles`, {
        method: "POST",
        headers,
        body: JSON.stringify({ user_id: userId, role, scope_type: scopeType }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(parseError(j));
      setOk("Role concedida.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/user-roles`));
    } finally {
      setLoading(false);
    }
  };

  const onRevoke = async (roleId) => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const res = await fetch(`${API}/user-roles/${encodeURIComponent(roleId)}/revoke`, { method: "POST", headers });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(parseError(j));
      setOk("Role revogada.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/user-roles/.../revoke`));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10, gap: 8 }}>
          <Link to="/ops/partners/admin" style={crossShortcutLinkStyle}>
            Parceiros admin
          </Link>
          <Link to="/ops/tenants/admin" style={crossShortcutLinkStyle}>
            Tenants
          </Link>
          <Link to="/ops/auth/policy" style={crossShortcutLinkStyle}>
            Politica de autorizacao
          </Link>
          <Link to="/ops/lockers/create" style={crossShortcutLinkStyle}>
            Criar lockers
          </Link>
        </div>

        <OpsPageTitleHeader
          title="OPS — Papéis (user_roles)"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Concessao e revogacao de roles — <code style={{ color: "#e2e8f0" }}>{API}/user-roles</code> — alinhado a{" "}
          <code style={{ color: "#e2e8f0" }}>public.user_roles</code>.
        </p>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Nova role</h3>
          </div>
          <div style={healthLocalFilterRowStyle}>
            <label style={healthLocalFilterFieldStyle}>
              user_id
              <select value={userId} onChange={(e) => setUserId(e.target.value)} style={healthLocalFilterInputStyle}>
                <option value="">— selecione —</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.email}
                  </option>
                ))}
              </select>
            </label>
            <label style={healthLocalFilterFieldStyle}>
              role
              <select value={role} onChange={(e) => setRole(e.target.value)} style={healthLocalFilterInputStyle}>
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </label>
            <label style={healthLocalFilterFieldStyle}>
              scope_type
              <input value={scopeType} onChange={(e) => setScopeType(e.target.value)} style={healthLocalFilterInputStyle} />
            </label>
          </div>
          <div style={toolbarStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => void load()} disabled={loading || !token}>
              {loading ? "Atualizando..." : "Listar"}
            </button>
            {canMutate ? (
              <button type="button" style={buttonPrimaryStyle} onClick={() => void onGrant()} disabled={loading || !userId}>
                Conceder role
              </button>
            ) : null}
          </div>
        </section>

        {err ? <div style={criticalBannerStyle} role="alert">{err}</div> : null}
        {ok ? <p style={okBannerStyle}>{ok}</p> : null}
        {!token ? <p style={summary24hHintStyle}>Faca login com perfil admin_operacao.</p> : null}
        {token && !canMutate ? <p style={summary24hHintStyle}>Escrita exige admin_operacao.</p> : null}

        {roles.length > 0 ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Roles ({roles.length})</h3>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["user_id", "role", "scope", "ativa", ""].map((h) => (
                      <th key={h} style={thStyle}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {roles.map((r) => (
                    <tr key={r.id}>
                      <td style={tdStyle}><code>{r.user_id}</code></td>
                      <td style={tdStyle}>{r.role}</td>
                      <td style={tdStyle}>
                        {r.scope_type}
                        {r.scope_id ? ` / ${r.scope_id}` : ""}
                      </td>
                      <td style={tdStyle}>{r.is_active && !r.revoked_at ? "Y" : "N"}</td>
                      <td style={tdStyle}>
                        {canMutate && r.is_active && !r.revoked_at ? (
                          <button type="button" style={buttonGhostStyle} onClick={() => void onRevoke(r.id)}>
                            Revogar
                          </button>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : token && !loading && !err ? (
          <p style={summary24hHintStyle}>Nenhuma role listada (use Seed em Parceiros admin).</p>
        ) : null}
      </section>
    </div>
  );
}

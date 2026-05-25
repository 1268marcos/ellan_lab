import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { securityCrudApi } from "../../api/securityCrud";
import {
  buttonGhostStyle,
  buttonPrimaryStyle,
  mutedTextStyle,
  okBannerStyle,
  tableStyle,
  tdStyle,
  thStyle,
  toolbarStyle,
} from "../../styles/opsShellStyles";

const ROLES = ["admin", "ops", "finance", "support", "partner"];

function useSecurityToken() {
  const { token } = useAuth();
  return token;
}

export function UsersList() {
  const token = useSecurityToken();
  const [users, setUsers] = useState([]);
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    try {
      const data = await securityCrudApi.listUsers(token);
      setUsers(data.users || []);
    } catch (e) {
      setErr(e.message);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div>
      <div style={toolbarStyle}>
        <Link to="/security/users/new" style={buttonPrimaryStyle}>
          Novo usuário
        </Link>
        <Link to="/security/roles" style={buttonGhostStyle}>
          Papéis
        </Link>
        <button type="button" style={buttonGhostStyle} onClick={() => void load()}>
          Atualizar
        </button>
      </div>
      {err && <p style={{ color: "#b91c1c" }}>{err}</p>}
      <table style={tableStyle}>
        <thead>
          <tr>
            <th style={thStyle}>Nome</th>
            <th style={thStyle}>E-mail</th>
            <th style={thStyle}>Ativo</th>
            <th style={thStyle} />
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td style={tdStyle}>{u.full_name}</td>
              <td style={tdStyle}>{u.email}</td>
              <td style={tdStyle}>{u.is_active ? "Sim" : "Não"}</td>
              <td style={tdStyle}>
                <Link to={`/security/users/${u.id}`}>Detalhe</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function UserForm() {
  const token = useSecurityToken();
  const { userId } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(userId);
  const [form, setForm] = useState({ full_name: "", email: "", phone: "", is_active: true });
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!userId) return;
    void securityCrudApi.getUser(token, userId).then((u) =>
      setForm({ full_name: u.full_name, email: u.email, phone: u.phone || "", is_active: u.is_active }),
    );
  }, [token, userId]);

  const onSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isEdit) {
        await securityCrudApi.updateUser(token, userId, form);
        navigate(`/security/users/${userId}`);
      } else {
        const u = await securityCrudApi.createUser(token, form);
        navigate(`/security/users/${u.id}`);
      }
    } catch (ex) {
      setErr(ex.message);
    }
  };

  return (
    <form onSubmit={(e) => void onSubmit(e)}>
      <h3>{isEdit ? "Editar usuário" : "Novo usuário"}</h3>
      <input value={form.full_name} onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} placeholder="Nome" />
      <input value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} placeholder="E-mail" />
      <button type="submit" style={buttonPrimaryStyle}>
        Salvar
      </button>
      {err && <p style={{ color: "#b91c1c" }}>{err}</p>}
    </form>
  );
}

export function UserDetail() {
  const token = useSecurityToken();
  const { userId } = useParams();
  const [user, setUser] = useState(null);
  const [roles, setRoles] = useState([]);

  useEffect(() => {
    if (!userId) return;
    void Promise.all([securityCrudApi.getUser(token, userId), securityCrudApi.listRoles(token, userId)]).then(
      ([u, r]) => {
        setUser(u);
        setRoles(r.roles || []);
      },
    );
  }, [token, userId]);

  if (!user) return <p style={mutedTextStyle}>Carregando…</p>;
  return (
    <div>
      <div style={toolbarStyle}>
        <Link to={`/security/users/${userId}/edit`} style={buttonPrimaryStyle}>
          Editar
        </Link>
        <Link to="/security/users" style={buttonGhostStyle}>
          Lista
        </Link>
      </div>
      <p>
        <strong>{user.full_name}</strong> — {user.email}
      </p>
      <ul>
        {roles.map((r) => (
          <li key={r.id}>
            <Link to={`/security/roles/${r.id}`}>{r.role}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function RolesList() {
  const token = useSecurityToken();
  const [roles, setRoles] = useState([]);
  useEffect(() => {
    void securityCrudApi.listRoles(token).then((d) => setRoles(d.roles || []));
  }, [token]);
  return (
    <div>
      <Link to="/security/roles/new" style={buttonPrimaryStyle}>
        Novo papel
      </Link>
      <table style={tableStyle}>
        <tbody>
          {roles.map((r) => (
            <tr key={r.id}>
              <td style={tdStyle}>{r.role}</td>
              <td style={tdStyle}>{r.user_id}</td>
              <td style={tdStyle}>
                <Link to={`/security/roles/${r.id}`}>Detalhe</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function RoleForm() {
  const token = useSecurityToken();
  const { roleId } = useParams();
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const [form, setForm] = useState({ user_id: search.get("user_id") || "", role: "ops", scope_type: "GLOBAL" });

  const onSubmit = async (e) => {
    e.preventDefault();
    const row = await securityCrudApi.createRole(token, form);
    navigate(`/security/roles/${row.id}`);
  };

  return (
    <form onSubmit={(e) => void onSubmit(e)}>
      <h3>{roleId ? "Editar papel" : "Novo papel"}</h3>
      <input value={form.user_id} onChange={(e) => setForm((f) => ({ ...f, user_id: e.target.value }))} placeholder="user_id" />
      <select value={form.role} onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}>
        {ROLES.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
      <button type="submit" style={buttonPrimaryStyle}>
        Salvar
      </button>
    </form>
  );
}

export function RoleDetail() {
  const token = useSecurityToken();
  const { roleId } = useParams();
  const [role, setRole] = useState(null);
  useEffect(() => {
    void securityCrudApi.getRole(token, roleId).then(setRole);
  }, [token, roleId]);
  if (!role) return null;
  return (
    <p>
      {role.role} — {role.user_id}
    </p>
  );
}

export function PermissionsMatrix() {
  const token = useSecurityToken();
  const [matrix, setMatrix] = useState(null);
  const load = useCallback(() => securityCrudApi.matrix(token).then(setMatrix), [token]);
  useEffect(() => {
    void load();
  }, [load]);
  return (
    <div>
      <button type="button" style={buttonGhostStyle} onClick={() => void securityCrudApi.seed(token).then(load)}>
        Seed
      </button>
      {(matrix?.groups || []).map((g) => (
        <div key={g.group_id} style={{ marginTop: 12 }}>
          <strong>{g.group_name}</strong>
          <ul>
            {g.permissions.map((p) => (
              <li key={p.id}>{p.object_key}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

export function ApiKeysManager() {
  const token = useSecurityToken();
  const [keys, setKeys] = useState([]);
  const [userId, setUserId] = useState("usr-admin");
  const [rotated, setRotated] = useState("");
  const load = useCallback(() => securityCrudApi.listApiKeys(token).then((d) => setKeys(d.items || [])), [token]);
  useEffect(() => {
    void load();
  }, [load]);
  return (
    <div>
      <input value={userId} onChange={(e) => setUserId(e.target.value)} />
      <button
        type="button"
        style={buttonPrimaryStyle}
        onClick={() =>
          void securityCrudApi.rotateApiKey(token, { user_id: userId }).then((d) => {
            setRotated(d.api_key);
            void load();
          })
        }
      >
        Rotacionar
      </button>
      {rotated && <p style={okBannerStyle}>Nova chave: {rotated}</p>}
      <table style={tableStyle}>
        <tbody>
          {keys.map((k) => (
            <tr key={k.id}>
              <td style={tdStyle}>{k.key_prefix}</td>
              <td style={tdStyle}>{k.user_id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function WebhookConfig() {
  const token = useSecurityToken();
  const [items, setItems] = useState([]);
  const [url, setUrl] = useState("https://hooks.example/ops");
  const [secret, setSecret] = useState("");
  useEffect(() => {
    void securityCrudApi.listWebhooks(token).then((d) => setItems(d.items || []));
  }, [token]);
  return (
    <div>
      <input value={url} onChange={(e) => setUrl(e.target.value)} style={{ width: "100%" }} />
      <button
        type="button"
        style={buttonPrimaryStyle}
        onClick={() =>
          void securityCrudApi.webhookConfig(token, { url, events: ["*"] }).then((d) => {
            if (d.webhook_secret) setSecret(d.webhook_secret);
          })
        }
      >
        Salvar webhook
      </button>
      {secret && <p style={okBannerStyle}>Secret: {secret}</p>}
      <ul>
        {items.map((w) => (
          <li key={w.id}>
            {w.url}
          </li>
        ))}
      </ul>
    </div>
  );
}

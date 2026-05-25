import React from "react";

const V1_PROFILES = [
  {
    id: "admin",
    label: "Administrador",
    scope: "Menu OPS completo (todos os grupos)",
    login: "http://localhost:5173/v1/login — API key",
  },
  {
    id: "ops",
    label: "Operações",
    scope: "Cadastros, hardware, pagamentos, fiscal OPS, marketplace, produtos, …",
    login: "http://localhost:5173/v1/login — API key",
  },
  {
    id: "partner",
    label: "Parceiro",
    scope: "Catálogo, webhooks, wallet, inteligência e runtime (sem blocos OPS internos)",
    login: "http://localhost:5173/v1/login — API key",
  },
];

const V0_ROLES = [
  {
    role: "admin_operacao",
    users: "admin.operacao@ellanlab.com",
    allowed: "/public/*, /dev-admin/*, /dev-admin/base/*",
    blocked: "—",
  },
  {
    role: "suporte",
    users: "suporte@ellanlab.com",
    allowed: "/public/*, /dev-admin/base/*",
    blocked: "/dev-admin/* (exceto base)",
  },
  {
    role: "auditoria",
    users: "auditoria@ellanlab.com",
    allowed: "/public/*, /dev-admin/*, /dev-admin/base/*",
    blocked: "—",
  },
  {
    role: "usuario_comum",
    users: "(sem role ativa em user_roles)",
    allowed: "/public/*",
    blocked: "/dev-admin/*, /dev-admin/base/*",
  },
];

const tableStyle = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: 13,
};

const thStyle = {
  textAlign: "left",
  padding: "8px 10px",
  borderBottom: "2px solid #e2e8f0",
  color: "#475569",
  fontWeight: 600,
};

const tdStyle = {
  padding: "8px 10px",
  borderBottom: "1px solid #f1f5f9",
  color: "#334155",
  verticalAlign: "top",
};

export default function AuthorizationAccessOverview() {
  return (
    <section style={{ display: "grid", gap: 20, marginBottom: 20 }}>
      <div
        style={{
          border: "1px solid #e2e8f0",
          borderRadius: 12,
          background: "#f8fafc",
          padding: 16,
        }}
      >
        <h3 style={{ margin: "0 0 8px", fontSize: 16 }}>Dois modelos de acesso</h3>
        <p style={{ margin: 0, color: "#475569", lineHeight: 1.5, fontSize: 14 }}>
          O <strong>portal v0</strong> (consumidor + OPS público) usa JWT e roles em{" "}
          <code>public.user_roles</code>. O <strong>console v1</strong> usa API key de parceiro
          com perfil <code>admin</code>, <code>ops</code> ou <code>partner</code> para filtrar o
          menu lateral.
        </p>
        <p style={{ margin: "10px 0 0", fontSize: 13, color: "#64748b" }}>
          <a href="http://localhost:5173/v1/login">Login OPS v1</a>
          {" · "}
          <a href="http://localhost:5174/v0/login">Login consumidor v0</a>
          {" · "}
          <a href="http://localhost:5174/v0/checkout?region=SP&locker_id=SP-ALPHAVILLE-SHOP-LK-001&sku_id=mini_cookie_iogurte&slot=8">
            Checkout exemplo
          </a>
        </p>
      </div>

      <div style={{ border: "1px solid #e2e8f0", borderRadius: 12, background: "#fff", padding: 16 }}>
        <h3 style={{ margin: "0 0 10px", fontSize: 16 }}>Portal v0 — roles (API pública)</h3>
        <div style={{ overflowX: "auto" }}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Role</th>
                <th style={thStyle}>Usuário exemplo</th>
                <th style={thStyle}>Permitido</th>
                <th style={thStyle}>Bloqueado</th>
              </tr>
            </thead>
            <tbody>
              {V0_ROLES.map((row) => (
                <tr key={row.role}>
                  <td style={tdStyle}>
                    <code>{row.role}</code>
                  </td>
                  <td style={tdStyle}>{row.users}</td>
                  <td style={tdStyle}>{row.allowed}</td>
                  <td style={tdStyle}>{row.blocked}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div style={{ border: "1px solid #e2e8f0", borderRadius: 12, background: "#fff", padding: 16 }}>
        <h3 style={{ margin: "0 0 10px", fontSize: 16 }}>Console v1 — perfis (menu lateral)</h3>
        <div style={{ overflowX: "auto" }}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Perfil</th>
                <th style={thStyle}>Escopo no menu</th>
                <th style={thStyle}>Login</th>
              </tr>
            </thead>
            <tbody>
              {V1_PROFILES.map((row) => (
                <tr key={row.id}>
                  <td style={tdStyle}>
                    <code>{row.id}</code> — {row.label}
                  </td>
                  <td style={tdStyle}>{row.scope}</td>
                  <td style={tdStyle}>{row.login}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import OpsPageTitleHeader from "../../components/OpsPageTitleHeader";
import { cardStyle, pageStyle } from "../../styles/opsShellStyles";

const NAV = [
  { to: "/security/users", label: "Users & Roles" },
  { to: "/security/permissions", label: "Permissions" },
  { to: "/security/api-keys", label: "API Keys" },
  { to: "/security/webhooks", label: "Webhooks" },
];

export default function SecurityShell() {
  return (
    <div style={pageStyle}>
      <OpsPageTitleHeader title="Security" subtitle="Users · Roles · Permissions · API Keys · Webhooks" />
      <div style={{ ...cardStyle, marginBottom: 12, display: "flex", flexWrap: "wrap", gap: 8 }}>
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            style={({ isActive }) => ({
              padding: "6px 12px",
              borderRadius: 6,
              textDecoration: "none",
              background: isActive ? "#4f46e5" : "#f3f4f6",
              color: isActive ? "#fff" : "#374151",
              fontSize: 13,
            })}
          >
            {item.label}
          </NavLink>
        ))}
        <NavLink to="/ops/access/security-admin?tab=overview" style={{ padding: "6px 12px", fontSize: 13, color: "#6b7280" }}>
          Hub legado
        </NavLink>
      </div>
      <div style={cardStyle}>
        <Outlet />
      </div>
    </div>
  );
}

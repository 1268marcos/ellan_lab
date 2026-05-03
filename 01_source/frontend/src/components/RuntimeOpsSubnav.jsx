import React from "react";
import { Link, useLocation } from "react-router-dom";
import { navLinkMutedStyle, navLinkStyle, navRowStyle } from "../utils/runtimeOpsPageChrome";

const LINKS = [
  { to: "/ops/runtime/health", label: "Runtime health" },
  { to: "/ops/runtime/events", label: "Event log" },
  { to: "/ops/runtime/slots", label: "Slots monitor" },
  { to: "/ops/runtime/sync", label: "Postgres sync" },
];

export default function RuntimeOpsSubnav() {
  const { pathname } = useLocation();
  return (
    <nav style={navRowStyle} aria-label="Navegação runtime OPS">
      {LINKS.map(({ to, label }) => (
        <Link
          key={to}
          to={to}
          style={{
            ...navLinkStyle,
            opacity: pathname === to ? 1 : 0.82,
            outline: pathname === to ? "1px solid rgba(147,197,253,0.5)" : "none",
          }}
        >
          {label}
        </Link>
      ))}
      <Link to="/ops/health" style={navLinkMutedStyle}>
        Stack ops/health
      </Link>
    </nav>
  );
}

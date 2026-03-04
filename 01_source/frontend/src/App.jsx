import React from "react";
import { Routes, Route, Navigate, Link } from "react-router-dom";
import LockerDashboard from "./pages/LockerDashboard.jsx";

export default function App() {
  return (
    <div>
      <nav
        style={{
          padding: 12,
          display: "flex",
          gap: 12,
          alignItems: "center",
          background: "#0b0d10",
          borderBottom: "1px solid rgba(255,255,255,0.10)",
        }}
      >
        <Link style={linkStyle} to="/sp">
          /sp
        </Link>
        <Link style={linkStyle} to="/pt">
          /pt
        </Link>

        <span style={{ marginLeft: 10, opacity: 0.65, color: "white", fontSize: 12 }}>
          Dashboard (gavetas 1–24 + carrossel 6×4)
        </span>
      </nav>

      <Routes>
        <Route path="/" element={<Navigate to="/sp" replace />} />
        <Route path="/sp" element={<LockerDashboard region="SP" />} />
        <Route path="/pt" element={<LockerDashboard region="PT" />} />
        <Route path="*" element={<div style={{ padding: 24 }}>404</div>} />
      </Routes>
    </div>
  );
}

const linkStyle = {
  color: "white",
  textDecoration: "none",
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.18)",
  background: "rgba(255,255,255,0.06)",
};
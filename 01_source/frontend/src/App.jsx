import React from "react";
import { Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import LockerDashboard from "./pages/LockerDashboard.jsx";
import RegionPage from "./pages/RegionPage.jsx";

export default function App() {
  const location = useLocation();

  const getNavBackground = () => {
    if (location.pathname.startsWith("/pt")) {
      return "linear-gradient(135deg, rgba(0,102,0,0.9) 0%, rgba(206,17,38,0.9) 70%)";
    }
    if (location.pathname.startsWith("/sp")) {
      return "linear-gradient(135deg, rgba(0,155,58,0.9) 0%, rgba(254,221,0,0.9) 50%, rgba(0,39,118,0.9) 100%)";
    }
    return "linear-gradient(135deg, #222324, #0b0d10)";
  };

  const getFlagEmoji = () => {
    if (location.pathname.startsWith("/pt")) return "🇵🇹";
    if (location.pathname.startsWith("/sp")) return "🇧🇷";
    return "";
  };

  const getContextLabel = () => {
    if (location.pathname.includes("/kiosk")) return "KIOSK Simulator";
    if (location.pathname === "/pt" || location.pathname === "/sp") return "Dashboard";
    return "ELLAN Lab Locker";
  };

  return (
    <div>
      <nav
        style={{
          padding: 12,
          display: "flex",
          gap: 12,
          alignItems: "center",
          background: getNavBackground(),
          borderBottom: "1px solid rgba(255,255,255,0.10)",
        }}
      >
        <Link style={linkStyle} to="/sp">
          /sp
        </Link>
        <Link style={linkStyle} to="/pt">
          /pt
        </Link>
        <Link style={linkStyle} to="/sp/kiosk">
          /sp/kiosk
        </Link>
        <Link style={linkStyle} to="/pt/kiosk">
          /pt/kiosk
        </Link>

        <span style={{ marginLeft: 10, opacity: 0.75, color: "white", fontSize: 12 }}>
          {getFlagEmoji()} {getContextLabel()}
        </span>
      </nav>

      <Routes>
        <Route path="/" element={<Navigate to="/sp" replace />} />

        <Route path="/sp" element={<LockerDashboard region="SP" />} />
        <Route path="/pt" element={<LockerDashboard region="PT" />} />

        <Route path="/sp/kiosk" element={<RegionPage region="SP" mode="kiosk" />} />
        <Route path="/pt/kiosk" element={<RegionPage region="PT" mode="kiosk" />} />

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
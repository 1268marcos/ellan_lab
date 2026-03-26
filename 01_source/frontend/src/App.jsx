// 01_source/frontend/src/App.jsx
import React from "react";
import { Routes, Route, Navigate, Link, useLocation, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";

import LockerDashboard from "./pages/LockerDashboard.jsx";
import RegionPage from "./pages/RegionPage.jsx";
import DevLockerResetPage from "./pages/DevLockerResetPage.jsx";
import PickupHealthPage from "./pages/PickupHealthPage.jsx";

import PublicLandingPage from "./pages/public/PublicLandingPage.jsx";
import PublicLoginPage from "./pages/public/PublicLoginPage.jsx";
import PublicRegisterPage from "./pages/public/PublicRegisterPage.jsx";
import PublicCatalogPage from "./pages/public/PublicCatalogPage.jsx";
import PublicCheckoutPage from "./pages/public/PublicCheckoutPage.jsx";
import PublicMyOrdersPage from "./pages/public/PublicMyOrdersPage.jsx";
import PublicOrderDetailPage from "./pages/public/PublicOrderDetailPage.jsx";
import PublicFiscalSearchPage from "./pages/public/PublicFiscalSearchPage.jsx";
import PublicRegionHubPage from "./pages/public/PublicRegionHubPage.jsx";

function initialsFromName(nameOrEmail) {
  const raw = (nameOrEmail || "").trim();
  if (!raw) return "?";

  const parts = raw.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0] || ""}${parts[1][0] || ""}`.toUpperCase();
  }

  return raw.slice(0, 2).toUpperCase();
}

function isOpsEnabled() {
  return String(import.meta.env.VITE_ENABLE_OPS_ROUTES || "").toLowerCase() === "true";
}

function TopNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout, loading } = useAuth();

  const fullName = user?.full_name || user?.email || "";
  const initials = initialsFromName(fullName);
  const opsEnabled = isOpsEnabled();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const getNavBackground = () => {
    if (location.pathname.startsWith("/ops")) {
      return "linear-gradient(135deg, rgba(138,35,35,0.95), rgba(70,10,10,0.95))";
    }
    if (location.pathname.startsWith("/pt")) {
      return "linear-gradient(135deg, rgba(0,102,0,0.9), rgba(206,17,38,0.9))";
    }
    if (location.pathname.startsWith("/sp")) {
      return "linear-gradient(135deg, rgba(0,155,58,0.9), rgba(254,221,0,0.9), rgba(0,39,118,0.9))";
    }
    return "linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d)";
  };

  return (
    <nav
      style={{
        padding: 12,
        display: "flex",
        alignItems: "center",
        gap: 10,
        flexWrap: "wrap",
        background: getNavBackground(),
        borderBottom: "1px solid rgba(255,255,255,0.1)",
      }}
    >
      <Link style={linkStyle} to="/">Início</Link>
      <Link style={linkStyle} to="/comprar">Comprar</Link>
      <Link style={linkStyle} to="/comprovante">Comprovante</Link>
      <Link style={linkStyle} to="/sp">SP</Link>
      <Link style={linkStyle} to="/pt">PT</Link>

      {!loading && isAuthenticated && (
        <Link style={linkStyle} to="/meus-pedidos">
          Meus Pedidos
        </Link>
      )}

      {opsEnabled && opsEnabled ? (
        <>
          <span style={separatorStyle}>|</span>
          <Link style={devLinkStyle} to="/ops/sp">ops /sp</Link>
          <Link style={devLinkStyle} to="/ops/pt">ops /pt</Link>
          <Link style={devLinkStyle} to="/ops/sp/kiosk">ops /sp/kiosk</Link>
          <Link style={devLinkStyle} to="/ops/pt/kiosk">ops /pt/kiosk</Link>
          <Link style={devLinkStyle} to="/ops/dev/reset">ops /dev/reset</Link>
          <Link style={devLinkStyle} to="/ops/analytics/pickup">ops /analytics/pickup</Link>
        </>
      ) : null}

      <div style={{ flex: 1 }} />

      {!loading && !isAuthenticated && (
        <>
          <Link style={linkStyle} to="/login">Entrar</Link>
          <Link style={linkStyle} to="/cadastro">Criar conta</Link>
        </>
      )}

      {!loading && isAuthenticated && (
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div
            title={fullName}
            style={{
              width: 36,
              height: 36,
              borderRadius: "50%",
              background: "rgba(255,255,255,0.15)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "white",
              fontWeight: "bold",
            }}
          >
            {initials}
          </div>

          <button onClick={handleLogout} style={logoutButtonStyle}>
            Sair
          </button>
        </div>
      )}
    </nav>
  );
}

function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <PageLoader />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function OpsRoute({ children }) {
  if (!isOpsEnabled()) {
    return <Navigate to="/" replace />;
  }
  return children;
}

function AppContent() {
  return (
    <div>
      <TopNav />

      <Routes>
        <Route path="/" element={<PublicLandingPage />} />
        <Route path="/login" element={<PublicLoginPage />} />
        <Route path="/cadastro" element={<PublicRegisterPage />} />
        <Route path="/comprar" element={<PublicCatalogPage />} />
        <Route path="/checkout" element={<PublicCheckoutPage />} />
        <Route path="/comprovante" element={<PublicFiscalSearchPage />} />

        <Route path="/sp" element={<PublicRegionHubPage region="SP" />} />
        <Route path="/pt" element={<PublicRegionHubPage region="PT" />} />

        <Route
          path="/meus-pedidos"
          element={
            <PrivateRoute>
              <PublicMyOrdersPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/meus-pedidos/:orderId"
          element={
            <PrivateRoute>
              <PublicOrderDetailPage />
            </PrivateRoute>
          }
        />

        <Route
          path="/ops/sp"
          element={
            <OpsRoute>
              <LockerDashboard region="SP" />
            </OpsRoute>
          }
        />
        <Route
          path="/ops/pt"
          element={
            <OpsRoute>
              <LockerDashboard region="PT" />
            </OpsRoute>
          }
        />
        <Route
          path="/ops/sp/kiosk"
          element={
            <OpsRoute>
              <RegionPage region="SP" mode="kiosk" />
            </OpsRoute>
          }
        />
        <Route
          path="/ops/pt/kiosk"
          element={
            <OpsRoute>
              <RegionPage region="PT" mode="kiosk" />
            </OpsRoute>
          }
        />
        <Route
          path="/ops/dev/reset"
          element={
            <OpsRoute>
              <DevLockerResetPage />
            </OpsRoute>
          }
        />
        <Route
          path="/ops/analytics/pickup"
          element={
            <OpsRoute>
              <PickupHealthPage />
            </OpsRoute>
          }
        />

        <Route path="*" element={<div style={{ padding: 24 }}>404</div>} />
      </Routes>
    </div>
  );
}

function PageLoader() {
  return (
    <div style={{ padding: 24 }}>
      <p style={{ color: "#666" }}>Carregando sessão...</p>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
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

const devLinkStyle = {
  ...linkStyle,
  border: "1px solid rgba(255,120,120,0.35)",
  background: "rgba(138,35,35,0.30)",
};

const separatorStyle = {
  color: "rgba(255,255,255,0.35)",
};

const logoutButtonStyle = {
  padding: "6px 10px",
  borderRadius: 8,
  border: "1px solid rgba(255,255,255,0.3)",
  background: "transparent",
  color: "white",
  cursor: "pointer",
};




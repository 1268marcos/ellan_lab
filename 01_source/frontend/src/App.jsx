import React from "react";
import { Routes, Route, Navigate, Link, useLocation, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";

// Importações existentes
import LockerDashboard from "./pages/LockerDashboard.jsx";
import RegionPage from "./pages/RegionPage.jsx";
import DevLockerResetPage from "./pages/DevLockerResetPage.jsx";
import PickupHealthPage from "./pages/PickupHealthPage.jsx";

// Públicas
import PublicLandingPage from "./pages/public/PublicLandingPage.jsx";
import PublicLoginPage from "./pages/public/PublicLoginPage.jsx";
import PublicRegisterPage from "./pages/public/PublicRegisterPage.jsx";
import PublicCatalogPage from "./pages/public/PublicCatalogPage.jsx";
import PublicCheckoutPage from "./pages/public/PublicCheckoutPage.jsx";
import PublicMyOrdersPage from "./pages/public/PublicMyOrdersPage.jsx";
import PublicOrderDetailPage from "./pages/public/PublicOrderDetailPage.jsx";

/* =========================================================
   HELPERS
========================================================= */

function initialsFromName(nameOrEmail) {
  const raw = (nameOrEmail || "").trim();
  if (!raw) return "?";

  const parts = raw.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0] || ""}${parts[1][0] || ""}`.toUpperCase();
  }

  return raw.slice(0, 2).toUpperCase();
}

/* =========================================================
   NAVBAR
========================================================= */

function TopNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout, loading } = useAuth();

  const fullName = user?.full_name || user?.email || "";
  const initials = initialsFromName(fullName);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const getNavBackground = () => {
    if (location.pathname.startsWith("/dev")) {
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
      {/* ÁREA PÚBLICA */}
      <Link style={linkStyle} to="/">Início</Link>
      <Link style={linkStyle} to="/comprar">Comprar</Link>

      {!loading && isAuthenticated && (
        <Link style={linkStyle} to="/meus-pedidos">
          Meus Pedidos
        </Link>
      )}

      {/* SEPARADOR */}
      <span style={separatorStyle}>|</span>

      {/* DEV / REGIONAL */}
      <Link style={linkStyle} to="/sp">/sp</Link>
      <Link style={linkStyle} to="/pt">/pt</Link>
      <Link style={linkStyle} to="/sp/kiosk">/sp/kiosk</Link>
      <Link style={linkStyle} to="/pt/kiosk">/pt/kiosk</Link>
      <Link style={devLinkStyle} to="/dev/reset">/dev/reset</Link>
      <Link style={devLinkStyle} to="/analytics/pickup">/analytics/pickup</Link>

      <div style={{ flex: 1 }} />

      {/* AUTH */}
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

/* =========================================================
   ROUTE PROTECTION
========================================================= */

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

/* =========================================================
   APP
========================================================= */

function AppContent() {
  return (
    <div>
      <TopNav />

      <Routes>
        {/* PÚBLICO */}
        <Route path="/" element={<PublicLandingPage />} />
        <Route path="/login" element={<PublicLoginPage />} />
        <Route path="/cadastro" element={<PublicRegisterPage />} />
        <Route path="/comprar" element={<PublicCatalogPage />} />
        <Route path="/checkout" element={<PublicCheckoutPage />} />

        {/* PROTEGIDO */}
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

        {/* REGIONAL */}
        <Route path="/sp" element={<LockerDashboard region="SP" />} />
        <Route path="/pt" element={<LockerDashboard region="PT" />} />
        <Route path="/sp/kiosk" element={<RegionPage region="SP" mode="kiosk" />} />
        <Route path="/pt/kiosk" element={<RegionPage region="PT" mode="kiosk" />} />

        {/* DEV */}
        <Route path="/dev/reset" element={<DevLockerResetPage />} />

        {/* ANALYTICS */}
        <Route path="/analytics/pickup" element={<PickupHealthPage />} />


        {/* 404 */}
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

/* =========================================================
   ROOT
========================================================= */

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

/* =========================================================
   STYLE
========================================================= */

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
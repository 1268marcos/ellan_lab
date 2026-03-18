import React from "react";
import { Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";

// Importações existentes
import LockerDashboard from "./pages/LockerDashboard.jsx";
import RegionPage from "./pages/RegionPage.jsx";
import DevLockerResetPage from "./pages/DevLockerResetPage.jsx";

// Novas importações públicas
import PublicLandingPage from "./pages/public/PublicLandingPage.jsx";
import PublicLoginPage from "./pages/public/PublicLoginPage.jsx";
import PublicRegisterPage from "./pages/public/PublicRegisterPage.jsx";
import PublicCatalogPage from "./pages/public/PublicCatalogPage.jsx";
import PublicCheckoutPage from "./pages/public/PublicCheckoutPage.jsx";
import PublicMyOrdersPage from "./pages/public/PublicMyOrdersPage.jsx";
import PublicOrderDetailPage from "./pages/public/PublicOrderDetailPage.jsx";

function AppContent() {
  const location = useLocation();

  const getNavBackground = () => {
    if (location.pathname.startsWith("/dev")) {
      return "linear-gradient(135deg, rgba(138,35,35,0.95) 0%, rgba(70,10,10,0.95) 100%)";
    }
    if (location.pathname.startsWith("/pt")) {
      return "linear-gradient(135deg, rgba(0,102,0,0.9) 0%, rgba(206,17,38,0.9) 70%)";
    }
    if (location.pathname.startsWith("/sp")) {
      return "linear-gradient(135deg, rgba(0,155,58,0.9) 0%, rgba(254,221,0,0.9) 50%, rgba(0,39,118,0.9) 100%)";
    }
    // Cores para rotas públicas
    if (location.pathname === "/" || 
        location.pathname.startsWith("/login") || 
        location.pathname.startsWith("/cadastro") ||
        location.pathname.startsWith("/comprar") ||
        location.pathname.startsWith("/checkout") ||
        location.pathname.startsWith("/meus-pedidos")) {
      return "linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d)";
    }
    return "linear-gradient(135deg, #222324, #0b0d10)";
  };

  const getFlagEmoji = () => {
    if (location.pathname.startsWith("/dev")) return "🛠️";
    if (location.pathname.startsWith("/pt")) return "🇵🇹";
    if (location.pathname.startsWith("/sp")) return "🇧🇷";
    if (location.pathname === "/" || location.pathname.startsWith("/login") || 
        location.pathname.startsWith("/cadastro") || location.pathname.startsWith("/comprar") ||
        location.pathname.startsWith("/checkout") || location.pathname.startsWith("/meus-pedidos")) {
      return "🏪";
    }
    return "";
  };

  const getContextLabel = () => {
    if (location.pathname.startsWith("/dev")) return "DEV Admin";
    if (location.pathname.includes("/kiosk")) return "KIOSK Simulator";
    if (location.pathname === "/pt" || location.pathname === "/sp") return "Dashboard";
    if (location.pathname === "/") return "ELLAN Store";
    if (location.pathname.startsWith("/login")) return "Login";
    if (location.pathname.startsWith("/cadastro")) return "Cadastro";
    if (location.pathname.startsWith("/comprar")) return "Catálogo";
    if (location.pathname.startsWith("/checkout")) return "Checkout";
    if (location.pathname.startsWith("/meus-pedidos")) {
      if (location.pathname.includes("/meus-pedidos/")) return "Detalhe do Pedido";
      return "Meus Pedidos";
    }
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
          flexWrap: "wrap",
          background: getNavBackground(),
          borderBottom: "1px solid rgba(255,255,255,0.10)",
        }}
      >
        {/* Links Públicos */}
        <Link style={linkStyle} to="/">
          Início
        </Link>
        <Link style={linkStyle} to="/login">
          Login
        </Link>
        <Link style={linkStyle} to="/cadastro">
          Cadastro
        </Link>
        <Link style={linkStyle} to="/comprar">
          Comprar
        </Link>
        <Link style={linkStyle} to="/meus-pedidos">
          Meus Pedidos
        </Link>

        {/* Separador visual */}
        <span style={{ color: "rgba(255,255,255,0.3)", margin: "0 5px" }}>|</span>

        {/* Links Regionais */}
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
        <Link style={devLinkStyle} to="/dev/reset">
          /dev/reset
        </Link>

        <span style={{ marginLeft: 10, opacity: 0.75, color: "white", fontSize: 12 }}>
          {getFlagEmoji()} {getContextLabel()}
        </span>
      </nav>

      <Routes>
        {/* Rotas Públicas */}
        <Route path="/" element={<PublicLandingPage />} />
        <Route path="/login" element={<PublicLoginPage />} />
        <Route path="/cadastro" element={<PublicRegisterPage />} />
        <Route path="/comprar" element={<PublicCatalogPage />} />
        <Route path="/checkout" element={<PublicCheckoutPage />} />
        <Route path="/meus-pedidos" element={<PublicMyOrdersPage />} />
        <Route path="/meus-pedidos/:orderId" element={<PublicOrderDetailPage />} />

        {/* Rotas Regionais */}
        <Route path="/sp" element={<LockerDashboard region="SP" />} />
        <Route path="/pt" element={<LockerDashboard region="PT" />} />

        <Route path="/sp/kiosk" element={<RegionPage region="SP" mode="kiosk" />} />
        <Route path="/pt/kiosk" element={<RegionPage region="PT" mode="kiosk" />} />

        {/* Rotas de Desenvolvimento */}
        <Route path="/dev/reset" element={<DevLockerResetPage />} />

        {/* Rota 404 */}
        <Route path="*" element={<div style={{ padding: 24 }}>404 - Página não encontrada</div>} />
      </Routes>
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
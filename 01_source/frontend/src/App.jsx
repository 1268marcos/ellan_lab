// 01_source/frontend/src/App.jsx
import React, { Suspense, lazy } from "react";
import { Routes, Route, Navigate, Link, useLocation, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";

// Lazy loading para performance
const PublicLandingPage = lazy(() => import("./pages/public/PublicLandingPage"));
const PublicLoginPage = lazy(() => import("./pages/public/PublicLoginPage"));
const PublicRegisterPage = lazy(() => import("./pages/public/PublicRegisterPage"));
const PublicCatalogPage = lazy(() => import("./pages/public/PublicCatalogPage"));
const PublicCheckoutPage = lazy(() => import("./pages/public/PublicCheckoutPage"));
const PublicMyOrdersPage = lazy(() => import("./pages/public/PublicMyOrdersPage"));
const PublicOrderDetailPage = lazy(() => import("./pages/public/PublicOrderDetailPage"));
const PublicFiscalSearchPage = lazy(() => import("./pages/public/PublicFiscalSearchPage"));
const PublicRegionHubPage = lazy(() => import("./pages/public/PublicRegionHubPage"));
const LockerDashboard = lazy(() => import("./pages/LockerDashboard"));
const RegionPage = lazy(() => import("./pages/RegionPage"));
const DevLockerResetPage = lazy(() => import("./pages/DevLockerResetPage"));
const PickupHealthPage = lazy(() => import("./pages/PickupHealthPage"));

// Componente de loading otimizado
function PageLoader() {
  return (
    <div className="page-loader" role="status" aria-live="polite">
      <div className="loader-spinner" aria-hidden="true"></div>
      <span className="sr-only">Carregando sessão...</span>
      <p className="loader-text">Carregando...</p>
    </div>
  );
}

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
      return "var(--nav-ops-bg)";
    }
    if (location.pathname.startsWith("/pt")) {
      return "var(--nav-pt-bg)";
    }
    if (location.pathname.startsWith("/sp")) {
      return "var(--nav-sp-bg)";
    }
    return "var(--nav-default-bg)";
  };

  return (
    <nav 
      className="top-nav" 
      style={{ background: getNavBackground() }}
      role="navigation"
      aria-label="Navegação principal"
    >
      <Link className="nav-link" to="/" aria-label="Ir para página inicial">Início</Link>
      <Link className="nav-link" to="/comprar" aria-label="Ver catálogo de produtos">Comprar</Link>
      <Link className="nav-link" to="/comprovante" aria-label="Consultar comprovante fiscal">Comprovante</Link>
      <Link className="nav-link" to="/sp" aria-label="Região São Paulo">SP</Link>
      <Link className="nav-link" to="/pt" aria-label="Região Portugal">PT</Link>
      
      {!loading && isAuthenticated && (
        <Link className="nav-link" to="/meus-pedidos" aria-label="Ver meus pedidos">
          Meus Pedidos
        </Link>
      )}
      
      {opsEnabled && (
        <div className="nav-divider" aria-hidden="true">|</div>
      )}
      
      {opsEnabled && (
        <div className="nav-ops-group" role="group" aria-label="Ferramentas operacionais">
          <Link className="nav-link nav-link--dev" to="/ops/sp">ops /sp</Link>
          <Link className="nav-link nav-link--dev" to="/ops/pt">ops /pt</Link>
          <Link className="nav-link nav-link--dev" to="/ops/dev/reset">ops /dev/reset</Link>
        </div>
      )}
      
      <div className="nav-spacer" aria-hidden="true" />
      
      {!loading && !isAuthenticated && (
        <div className="nav-auth-group" role="group" aria-label="Autenticação">
          <Link className="nav-link nav-link--primary" to="/login">Entrar</Link>
          <Link className="nav-link nav-link--secondary" to="/cadastro">Criar conta</Link>
        </div>
      )}
      
      {!loading && isAuthenticated && (
        <div className="nav-user-group" role="group" aria-label="Conta do usuário">
          <div
            className="user-avatar"
            title={fullName}
            aria-label={`Conta de ${fullName}`}
            role="img"
          >
            {initials}
          </div>
          <button 
            onClick={handleLogout} 
            className="nav-button nav-button--logout"
            aria-label="Sair da conta"
          >
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
    <div className="app-container">
      <TopNav />
      <main id="main-content" role="main">
        <Suspense fallback={<PageLoader />}>
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
            <Route 
              path="*" 
              element={
                <div className="error-page" role="alert">
                  <h1>404</h1>
                  <p>Página não encontrada</p>
                  <Link to="/" className="btn btn--primary">Voltar ao início</Link>
                </div>
              } 
            />
          </Routes>
        </Suspense>
      </main>
      <footer className="app-footer" role="contentinfo">
        <p>&copy; {new Date().getFullYear()} ELLAN Lab Locker. Todos os direitos reservados.</p>
      </footer>
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
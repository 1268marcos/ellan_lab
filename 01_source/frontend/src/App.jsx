// 01_source/frontend/src/App.jsx
import React, { Suspense, lazy, useState, useEffect, useRef } from "react";
import { Routes, Route, Navigate, Link, useLocation, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import {
  clearRuntimeGeoScopeTenantOverride,
  getRuntimeGeoScopeTenantOverride,
} from "./utils/lockerGeoFilter";

// Lazy loading para performance
const PublicLandingPage = lazy(() => import("./pages/public/PublicLandingPage"));
const PublicLoginPage = lazy(() => import("./pages/public/PublicLoginPage"));
const PublicRegisterPage = lazy(() => import("./pages/public/PublicRegisterPage"));
const PublicForgotPasswordPage = lazy(() => import("./pages/public/PublicForgotPasswordPage"));
const PublicCatalogPage = lazy(() => import("./pages/public/PublicCatalogPage"));
const PublicCheckoutPage = lazy(() => import("./pages/public/PublicCheckoutPage"));
const PublicMyOrdersPage = lazy(() => import("./pages/public/PublicMyOrdersPage"));
const PublicMyCreditsPage = lazy(() => import("./pages/public/PublicMyCreditsPage"));
const PublicSecurityPage = lazy(() => import("./pages/public/PublicSecurityPage"));
const PublicFiscalDataPage = lazy(() => import("./pages/public/PublicFiscalDataPage"));
const PublicOrderDetailPage = lazy(() => import("./pages/public/PublicOrderDetailPage"));
const PublicEmailVerificationPage = lazy(() => import("./pages/public/PublicEmailVerificationPage"));
const PublicFiscalSearchPage = lazy(() => import("./pages/public/PublicFiscalSearchPage"));
const PublicRegionHubPage = lazy(() => import("./pages/public/PublicRegionHubPage"));
const PublicNotFoundPage = lazy(() => import("./pages/public/PublicNotFoundPage"));
const PublicSupportPage = lazy(() => import("./pages/public/PublicSupportPage")); // NOVA IMPORT
const PublicPrivacyPolicyPage = lazy(() => import("./pages/public/PublicPrivacyPolicyPage"));
const PublicTermsOfUsePage = lazy(() => import("./pages/public/PublicTermsOfUsePage"));
const PublicAccessDeniedPage = lazy(() => import("./pages/public/PublicAccessDeniedPage"));
const LockerDashboard = lazy(() => import("./pages/LockerDashboard"));
const LockerDashboardFirst = lazy(() => import("./pages/LockerDashboardFirst"));
const RegionPage = lazy(() => import("./pages/RegionPage"));
const RegionPageFirst = lazy(() => import("./pages/RegionPageFirst"));
const DevLockerResetPage = lazy(() => import("./pages/DevLockerResetPage"));
const DevSlotAllocationPage = lazy(() => import("./pages/DevSlotAllocationPage"));
const DevBaseCatalogPage = lazy(() => import("./pages/DevBaseCatalogPage"));
const PickupHealthPage = lazy(() => import("./pages/PickupHealthPage"));
const OpsAuthorizationPolicyPage = lazy(() => import("./pages/OpsAuthorizationPolicyPage"));
const OpsVersioningPolicyPage = lazy(() => import("./pages/OpsVersioningPolicyPage"));
const OpsReconciliationPage = lazy(() => import("./pages/OpsReconciliationPage"));
const OpsHealthPage = lazy(() => import("./pages/OpsHealthPage"));
const OpsAuditPage = lazy(() => import("./pages/OpsAuditPage"));
const OpsFiscalProvidersPage = lazy(() => import("./pages/OpsFiscalProvidersPage"));
const OpsPartnersDashboardPage = lazy(() => import("./pages/OpsPartnersDashboardPage"));
const OpsLogisticsDashboardPage = lazy(() => import("./pages/OpsLogisticsDashboardPage"));
const OpsLogisticsReturnsPage = lazy(() => import("./pages/OpsLogisticsReturnsPage"));
const OpsLogisticsManifestsPage = lazy(() => import("./pages/OpsLogisticsManifestsPage"));
const OpsLogisticsManifestsOverviewPage = lazy(() => import("./pages/OpsLogisticsManifestsOverviewPage"));
const OpsUpdatesHistoryPage = lazy(() => import("./pages/OpsUpdatesHistoryPage"));
const OpsProductsCatalogPage = lazy(() => import("./pages/OpsProductsCatalogPage"));
const OpsProductsAssetsPage = lazy(() => import("./pages/OpsProductsAssetsPage"));
const OpsProductsPricingFiscalPage = lazy(() => import("./pages/OpsProductsPricingFiscalPage"));
const OpsProductsInventoryHealthPage = lazy(() => import("./pages/OpsProductsInventoryHealthPage"));
const OpsIntegrationOutboxReplayPage = lazy(() => import("./pages/OpsIntegrationOutboxReplayPage"));
const OpsIntegrationOrdersFiscalPage = lazy(() => import("./pages/OpsIntegrationOrdersFiscalPage"));
const OpsIntegrationOrdersPartnerLookupPage = lazy(() => import("./pages/OpsIntegrationOrdersPartnerLookupPage"));
const OpsPartnersFinancialsServiceAreasPage = lazy(() => import("./pages/OpsPartnersFinancialsServiceAreasPage"));
const OpsPartnersReconciliationDashboardPage = lazy(() => import("./pages/OpsPartnersReconciliationDashboardPage"));
const OpsPartnersBillingMonitoringPage = lazy(() => import("./pages/OpsPartnersBillingMonitoringPage"));
const OpsPartnersHypertablesPage = lazy(() => import("./pages/OpsPartnersHypertablesPage"));

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
  const { user, isAuthenticated, logout, loading, hasRole } = useAuth();
  const fullName = user?.full_name || user?.email || "";
  const initials = initialsFromName(fullName);
  const opsEnabled = isOpsEnabled();
  const canAccessOps =
    isAuthenticated && (hasRole("admin_operacao") || hasRole("suporte") || hasRole("auditoria"));
  
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isOpsMenuOpen, setIsOpsMenuOpen] = useState(false);
  const [isMyAreaMenuOpen, setIsMyAreaMenuOpen] = useState(false);
  const [isMobileOpsOpen, setIsMobileOpsOpen] = useState(false);
  const [isMobileMyAreaOpen, setIsMobileMyAreaOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [tenantOverride, setTenantOverride] = useState("");
  const menuRef = useRef(null);
  const buttonRef = useRef(null);
  const opsMenuRef = useRef(null);
  const opsButtonRef = useRef(null);
  const myAreaMenuRef = useRef(null);
  const myAreaButtonRef = useRef(null);
  const envTenant = String(import.meta.env.VITE_GEO_SCOPE_TENANT || "").trim().toUpperCase();
  const hasTenantOverride = Boolean(tenantOverride);
  const isOpsRoute = location.pathname.startsWith("/ops");

  // Detectar tamanho da tela
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
      if (window.innerWidth > 768) {
        setIsMobileMenuOpen(false); // Fecha menu ao redimensionar para desktop
      }
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Fechar menu ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isMobileMenuOpen && 
          menuRef.current && 
          !menuRef.current.contains(event.target) &&
          buttonRef.current && 
          !buttonRef.current.contains(event.target)) {
        setIsMobileMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isMobileMenuOpen]);

  useEffect(() => {
    const handleOpsClickOutside = (event) => {
      if (
        isOpsMenuOpen &&
        opsMenuRef.current &&
        !opsMenuRef.current.contains(event.target) &&
        opsButtonRef.current &&
        !opsButtonRef.current.contains(event.target)
      ) {
        setIsOpsMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handleOpsClickOutside);
    return () => document.removeEventListener("mousedown", handleOpsClickOutside);
  }, [isOpsMenuOpen]);

  useEffect(() => {
    const handleMyAreaClickOutside = (event) => {
      if (
        isMyAreaMenuOpen &&
        myAreaMenuRef.current &&
        !myAreaMenuRef.current.contains(event.target) &&
        myAreaButtonRef.current &&
        !myAreaButtonRef.current.contains(event.target)
      ) {
        setIsMyAreaMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handleMyAreaClickOutside);
    return () => document.removeEventListener("mousedown", handleMyAreaClickOutside);
  }, [isMyAreaMenuOpen]);

  // Prevenir scroll do body quando menu estiver aberto
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isMobileMenuOpen]);

  useEffect(() => {
    if (!isMobileMenuOpen) return;

    const handleEscape = (event) => {
      if (event.key === "Escape") {
        setIsMobileMenuOpen(false);
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isMobileMenuOpen]);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
    setIsMobileMenuOpen(false);
  };

  const handleClearTenantOverride = () => {
    clearRuntimeGeoScopeTenantOverride();
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

  // Fechar menu ao navegar
  useEffect(() => {
    setIsMobileMenuOpen(false);
    setIsOpsMenuOpen(false);
    setIsMyAreaMenuOpen(false);
    setIsMobileOpsOpen(false);
    setIsMobileMyAreaOpen(false);
  }, [location]);

  useEffect(() => {
    const syncTenantOverride = () => {
      setTenantOverride(getRuntimeGeoScopeTenantOverride());
    };

    syncTenantOverride();
    window.addEventListener("ellan:geo-tenant-changed", syncTenantOverride);
    window.addEventListener("storage", syncTenantOverride);
    return () => {
      window.removeEventListener("ellan:geo-tenant-changed", syncTenantOverride);
      window.removeEventListener("storage", syncTenantOverride);
    };
  }, []);

  // Links comuns para todos os usuários
  const publicLinks = [
    { to: "/", label: "Início", aria: "Ir para página inicial" },
    { to: "/comprar", label: "Comprar", aria: "Ver catálogo de produtos" },
    { to: "/comprovante", label: "Comprovante", aria: "Consultar comprovante fiscal" },
    { to: "/suporte", label: "Suporte", aria: "Central de ajuda e suporte" }, // NOVO LINK
    { to: "/sp", label: "SP", aria: "Região São Paulo" },
    { to: "/pt", label: "PT", aria: "Região Portugal" }
  ];

  // Links de operação
  const opsLinks = opsEnabled ? [
    { to: "/ops/sp", label: "ops /sp", aria: "Ferramentas operacionais São Paulo", group: "Visão Geral" },
    { to: "/ops/pt", label: "ops /pt", aria: "Ferramentas operacionais Portugal", group: "Visão Geral" },
    { to: "/ops/sp/kiosk", label: "ops /sp/kiosk", aria: "Kiosk São Paulo", group: "Visão Geral" },
    { to: "/ops/pt/kiosk", label: "ops /pt/kiosk", aria: "Kiosk Portugal", group: "Visão Geral" },
    { to: "/ops/health", label: "ops /health", aria: "Saúde operacional e alertas", group: "Dashboards" },
    { to: "/ops/audit", label: "ops /audit", aria: "Trilha de auditoria operacional", group: "Dashboards" },
    { to: "/ops/reconciliation", label: "ops /reconciliation", aria: "Reconciliação operacional por order_id", group: "Dashboards" },
    { to: "/ops/updates", label: "ops /updates", aria: "Historico de acrescimos operacionais", group: "Dashboards" },
    { to: "/ops/analytics/pickup", label: "ops /analytics/pickup", aria: "Analytics de retirada", group: "Dashboards" },
    { to: "/ops/logistics/dashboard", label: "ops /logistics/dashboard", aria: "Dashboard OPS de Logistics", group: "Logística" },
    { to: "/ops/logistics/manifests", label: "ops /logistics/manifests", aria: "Operacao OPS de manifestos L3/D2", group: "Logística" },
    { to: "/ops/logistics/manifests-overview", label: "ops /logistics/manifests-overview", aria: "Overview OPS de manifestos L3/D3", group: "Logística" },
    { to: "/ops/logistics/returns", label: "ops /logistics/returns", aria: "Dashboard OPS de Returns", group: "Logística" },
    { to: "/ops/products/catalog", label: "ops /products/catalog", aria: "Dashboard OPS de Catalogo de produtos", group: "Produtos & Fiscal" },
    { to: "/ops/products/assets", label: "ops /products/assets", aria: "Operacao OPS para media e barcodes de produtos", group: "Produtos & Fiscal" },
    { to: "/ops/products/pricing-fiscal", label: "ops /products/pricing-fiscal", aria: "Operacao OPS para pricing e fiscal do Pr-3", group: "Produtos & Fiscal" },
    { to: "/ops/products/inventory-health", label: "ops /products/inventory-health", aria: "Dashboard OPS de Inventory Health", group: "Produtos & Fiscal" },
    { to: "/ops/fiscal/providers", label: "ops /fiscal/providers", aria: "Status de providers fiscais BR/PT", group: "Produtos & Fiscal" },
    { to: "/ops/integration/outbox-replay", label: "ops /integration/outbox-replay", aria: "Operacao de replay em lote do outbox de integracao", group: "Integrações" },
    { to: "/ops/integration/orders-fiscal", label: "ops /integration/orders-fiscal", aria: "Operacao I-1 por order_id (fulfillment, events, fiscal)", group: "Integrações" },
    { to: "/ops/integration/orders-partner-lookup", label: "ops /integration/orders-partner-lookup", aria: "Operacao L-3 para lookup dedicado por partner/ref", group: "Integrações" },
    { to: "/ops/partners/dashboard", label: "ops /partners/dashboard", aria: "Dashboard OPS de Partners", group: "Partners" },
    { to: "/ops/partners/financials-service-areas", label: "ops /partners/financials-service-areas", aria: "Operacao P-3 para settlements, performance e service-areas", group: "Partners" },
    { to: "/ops/partners/reconciliation-dashboard", label: "ops /partners/reconciliation-dashboard", aria: "Dashboard operacional de reconciliacao de settlements", group: "Partners" },
    { to: "/ops/partners/billing-monitor", label: "ops /partners/billing-monitor", aria: "Monitor simples de billing e invoices de partners", group: "Partners" },
    { to: "/ops/partners/hypertables", label: "ops /partners/hypertables", aria: "Status de hypertables e policies Timescale FA-5", group: "Partners" },
    { to: "/ops/auth/policy", label: "ops /auth/policy", aria: "Política de autorização operacional", group: "Políticas" },
    { to: "/ops/auth/policy/versioning", label: "ops /auth/policy/versioning", aria: "Política de versionamento da ops/health", group: "Políticas" },
    { to: "/ops/dev/reset", label: "ops /dev/reset", aria: "Reset de desenvolvimento", group: "Dev" },
    { to: "/ops/dev/slots", label: "ops /dev/slots", aria: "Alocação de produtos por slot", group: "Dev" },
    { to: "/ops/dev/base", label: "ops /dev/base (db)", aria: "Gestão de tabelas e enums base", group: "Dev" }
  ] : [];
  const opsGroupOrder = [
    "Visão Geral",
    "Dashboards",
    "Logística",
    "Produtos & Fiscal",
    "Integrações",
    "Partners",
    "Políticas",
    "Dev",
  ];
  const groupedOpsLinks = opsGroupOrder
    .map((group) => ({
      group,
      links: opsLinks.filter((link) => link.group === group),
    }))
    .filter((entry) => entry.links.length > 0);

  const myAreaLinks = [
    { to: "/meus-pedidos", label: "Meus Pedidos", aria: "Ver meus pedidos" },
    { to: "/meus-creditos", label: "Meus Créditos", aria: "Ver meus créditos" },
    { to: "/seguranca", label: "Segurança", aria: "Gerenciar segurança da conta" },
    { to: "/conta/dados-fiscais", label: "Dados fiscais", aria: "Dados fiscais da conta" },
  ];

  return (
    <>
      <a href="#main-content" className="skip-link">
        Pular para o conteudo principal
      </a>
      <nav 
        className="top-nav" 
        style={{ background: getNavBackground() }}
        role="navigation"
        aria-label="Navegação principal"
      >
        {/* Logo ou marca */}
        <div className="nav-brand">
          <Link to="/" className="nav-brand-link">
            ELLAN Lab
          </Link>
        </div>

        {/* Menu Desktop - visível apenas em telas grandes */}
        <div className="nav-desktop">
          {publicLinks.map(link => (
            <Link key={link.to} className="nav-link" to={link.to}>
              {link.label}
            </Link>
          ))}
          
          {!loading && isAuthenticated && (
            <div
              className="nav-ops-dropdown"
              role="group"
              aria-label="Minha Área"
              ref={myAreaMenuRef}
            >
              <button
                ref={myAreaButtonRef}
                type="button"
                className="nav-link nav-ops-toggle"
                onClick={() => setIsMyAreaMenuOpen((value) => !value)}
                aria-haspopup="menu"
                aria-expanded={isMyAreaMenuOpen}
              >
                Minha Área ({myAreaLinks.length}) {isMyAreaMenuOpen ? "▲" : "▼"}
              </button>
              {isMyAreaMenuOpen ? (
                <div className="nav-ops-panel" role="menu" aria-label="Menu Minha Área">
                  {myAreaLinks.map(link => (
                    <Link
                      key={link.to}
                      className="nav-ops-item"
                      to={link.to}
                      onClick={() => setIsMyAreaMenuOpen(false)}
                    >
                      {link.label}
                    </Link>
                  ))}
                </div>
              ) : null}
            </div>
          )}
          
          {opsEnabled && canAccessOps && opsLinks.length > 0 && (
            <>
              <div className="nav-divider" aria-hidden="true">|</div>
              <div
                className="nav-ops-dropdown"
                role="group"
                aria-label="Ferramentas operacionais"
                ref={opsMenuRef}
              >
                <button
                  ref={opsButtonRef}
                  type="button"
                  className="nav-link nav-link--dev nav-ops-toggle"
                  onClick={() => setIsOpsMenuOpen((value) => !value)}
                  aria-haspopup="menu"
                  aria-expanded={isOpsMenuOpen}
                >
                  OPS menu ({opsLinks.length}) {isOpsMenuOpen ? "▲" : "▼"}
                </button>
                {isOpsMenuOpen ? (
                  <div className="nav-ops-panel" role="menu" aria-label="Menu OPS">
                    {groupedOpsLinks.map((groupEntry) => (
                      <div key={groupEntry.group}>
                        <div className="ops-group-title">
                          {groupEntry.group}
                        </div>
                        {groupEntry.links.map(link => (
                          <Link
                            key={link.to}
                            className="nav-ops-item"
                            to={link.to}
                            onClick={() => setIsOpsMenuOpen(false)}
                          >
                            <span>{link.label}</span>
                            {link.isNew ? <span className="nav-new-badge">NEW</span> : null}
                          </Link>
                        ))}
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            </>
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
                aria-label={fullName ? `Conta de ${fullName}` : "Conta"}
                role="img"
              >
                {initials}
              </div>
              <button 
                onClick={handleLogout} 
                className="nav-button nav-button--logout"
                aria-label="Sair"
              >
                Sair
              </button>
            </div>
          )}
        </div>

        {/* Menu Mobile - Hambúrguer */}
        <div className="nav-mobile">
          {!loading && isAuthenticated && (
            <div className="mobile-user-info">
              <div className="user-avatar-mobile" title={fullName}>
                {initials}
              </div>
            </div>
          )}
          
          <button
            ref={buttonRef}
            type="button"
            className={`hamburger-menu ${isMobileMenuOpen ? 'active' : ''}`}
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label={isMobileMenuOpen ? "Fechar menu" : "Abrir menu"}
            aria-expanded={isMobileMenuOpen}
            aria-controls="mobile-menu"
            aria-haspopup="dialog"
          >
            <span className="hamburger-line"></span>
            <span className="hamburger-line"></span>
            <span className="hamburger-line"></span>
          </button>
        </div>
      </nav>

      {isOpsRoute && (
        <div
          style={{
            margin: "8px 16px 0",
            padding: "10px 12px",
            borderRadius: 12,
            border: "1px solid rgba(96, 165, 250, 0.35)",
            background: "linear-gradient(135deg, rgba(15,23,42,0.92), rgba(30,41,59,0.92))",
            boxShadow: "0 6px 18px rgba(2, 6, 23, 0.35)",
            display: "inline-flex",
            width: "fit-content",
            maxWidth: "calc(100% - 32px)",
            gap: 10,
            alignItems: "center",
            justifyContent: "flex-start",
            flexWrap: "wrap",
          }}
        >
          <div style={{ fontSize: 12, color: "#f8fafc", display: "flex", gap: 12, flexWrap: "wrap" }}>
            <span><b style={{ color: "#bfdbfe" }}>Contexto Ops</b></span>
            <span>Tenant env: <b style={{ color: "#e2e8f0" }}>{envTenant || "-"}</b></span>
            <span>
              Tenant ativo:{" "}
              <b style={{ color: hasTenantOverride ? "#fde68a" : "#f1f5f9" }}>
                {tenantOverride || envTenant || "-"}
              </b>
            </span>
            {hasTenantOverride ? (
              <span
                style={{
                  padding: "2px 8px",
                  borderRadius: 999,
                  border: "1px solid rgba(245, 158, 11, 0.45)",
                  background: "rgba(245, 158, 11, 0.18)",
                  color: "#fde68a",
                  fontWeight: 700,
                }}
              >
                Override ativo
              </span>
            ) : null}
          </div>

          {hasTenantOverride ? (
            <button
              onClick={handleClearTenantOverride}
              style={{
                padding: "8px 12px",
                borderRadius: 10,
                border: "1px solid rgba(245, 158, 11, 0.45)",
                background: "rgba(245, 158, 11, 0.18)",
                color: "#fde68a",
                cursor: "pointer",
                fontWeight: 700,
              }}
              title="Remover tenant override e voltar ao tenant do .env"
            >
              Limpar override
            </button>
          ) : null}
        </div>
      )}

      {/* Overlay do menu mobile */}
      {isMobileMenuOpen && (
        <div
          className="mobile-menu-overlay"
          onClick={() => setIsMobileMenuOpen(false)}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              setIsMobileMenuOpen(false);
            }
          }}
          role="button"
          tabIndex={0}
          aria-label="Fechar menu de navegacao movel"
        >
          <div 
            ref={menuRef}
            className="mobile-menu"
            id="mobile-menu"
            role="dialog"
            aria-modal="true"
            aria-labelledby="mobile-menu-title"
            aria-label="Menu de navegação móvel"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mobile-menu-header">
              <h2 id="mobile-menu-title" className="sr-only">Menu de navegacao</h2>
              {!loading && isAuthenticated && (
                <div className="mobile-user-details">
                  <div className="user-avatar-large">{initials}</div>
                  <div className="user-name">{fullName}</div>
                </div>
              )}
              {!loading && !isAuthenticated && (
                <div className="mobile-auth-buttons">
                  <Link to="/login" className="mobile-nav-link mobile-nav-link--primary" onClick={() => setIsMobileMenuOpen(false)}>
                    Entrar
                  </Link>
                  <Link to="/cadastro" className="mobile-nav-link mobile-nav-link--secondary" onClick={() => setIsMobileMenuOpen(false)}>
                    Criar conta
                  </Link>
                </div>
              )}
            </div>

            <div className="mobile-menu-content">
              {/* Links principais */}
              <div className="mobile-menu-section">
                <h3 className="mobile-menu-section-title">Navegação</h3>
                {publicLinks.map(link => (
                  <Link 
                    key={link.to} 
                    className="mobile-nav-link" 
                    to={link.to} 
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    {link.label}
                  </Link>
                ))}
                
              </div>

              {!loading && isAuthenticated && (
                <div className="mobile-menu-section">
                  <button
                    type="button"
                    className="mobile-ops-toggle"
                    onClick={() => setIsMobileMyAreaOpen((value) => !value)}
                    aria-expanded={isMobileMyAreaOpen}
                  >
                    Minha Área ({myAreaLinks.length}) {isMobileMyAreaOpen ? "▲" : "▼"}
                  </button>
                  {isMobileMyAreaOpen ? (
                    <div className="mobile-ops-list">
                      {myAreaLinks.map(link => (
                        <Link
                          key={link.to}
                          className="mobile-nav-link"
                          to={link.to}
                          onClick={() => setIsMobileMenuOpen(false)}
                        >
                          <span>{link.label}</span>
                          {link.isNew ? <span className="nav-new-badge">NEW</span> : null}
                        </Link>
                      ))}
                    </div>
                  ) : null}
                </div>
              )}

              {/* Links de operação */}
              {opsEnabled && canAccessOps && opsLinks.length > 0 && (
                <div className="mobile-menu-section">
                  <button
                    type="button"
                    className="mobile-ops-toggle"
                    onClick={() => setIsMobileOpsOpen((value) => !value)}
                    aria-expanded={isMobileOpsOpen}
                  >
                    Ferramentas Operacionais ({opsLinks.length}) {isMobileOpsOpen ? "▲" : "▼"}
                  </button>
                  {isMobileOpsOpen ? (
                    <div className="mobile-ops-list">
                      {groupedOpsLinks.map((groupEntry) => (
                        <div key={groupEntry.group}>
                          <div className="ops-group-title ops-group-title--mobile">
                            {groupEntry.group}
                          </div>
                          {groupEntry.links.map(link => (
                            <Link 
                              key={link.to} 
                              className="mobile-nav-link mobile-nav-link--dev" 
                              to={link.to} 
                              onClick={() => setIsMobileMenuOpen(false)}
                            >
                              <span>{link.label}</span>
                              {link.isNew ? <span className="nav-new-badge">NEW</span> : null}
                            </Link>
                          ))}
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              )}

              {/* Botão de logout para usuários autenticados */}
              {!loading && isAuthenticated && (
                <div className="mobile-menu-section">
                  <button 
                    onClick={handleLogout} 
                    className="mobile-logout-button"
                  >
                    Sair
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
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
  const { isAuthenticated, loading, hasRole } = useAuth();
  if (!isOpsEnabled()) {
    return <Navigate to="/" replace />;
  }
  if (loading) {
    return <PageLoader />;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  const allowed =
    hasRole("admin_operacao") || hasRole("suporte") || hasRole("auditoria");
  if (!allowed) {
    return <Navigate to="/acesso-negado" replace />;
  }
  return children;
}

function AppContent() {
  return (
    <div className="app-container">
      <TopNav />
      <div id="main-content">
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<PublicLandingPage />} />
            <Route path="/login" element={<PublicLoginPage />} />
            <Route path="/recuperar-senha" element={<PublicForgotPasswordPage />} />
            <Route path="/cadastro" element={<PublicRegisterPage />} />
            <Route path="/comprar" element={<PublicCatalogPage />} />
            <Route path="/checkout" element={<PublicCheckoutPage />} />
            <Route path="/comprovante" element={<PublicFiscalSearchPage />} />
            <Route path="/suporte" element={<PublicSupportPage />} /> {/* NOVA ROTA */}
            <Route path="/privacidade" element={<PublicPrivacyPolicyPage />} />
            <Route path="/termos" element={<PublicTermsOfUsePage />} />
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
              path="/meus-creditos"
              element={
                <PrivateRoute>
                  <PublicMyCreditsPage />
                </PrivateRoute>
              }
            />
            <Route
              path="/seguranca"
              element={
                <PrivateRoute>
                  <PublicSecurityPage />
                </PrivateRoute>
              }
            />
            <Route
              path="/conta/dados-fiscais"
              element={
                <PrivateRoute>
                  <PublicFiscalDataPage />
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
            <Route path="/verificar-email" element={<PublicEmailVerificationPage />} />
            <Route path="/acesso-negado" element={<PublicAccessDeniedPage />} />
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
              path="/ops/00"
              element={
                <OpsRoute>
                  <LockerDashboardFirst region="SP" />
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
              path="/ops/00/kiosk"
              element={
                <OpsRoute>
                  <RegionPageFirst region="SP" mode="kiosk" />
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
              path="/ops/dev/slots"
              element={
                <OpsRoute>
                  <DevSlotAllocationPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/dev/base"
              element={
                <OpsRoute>
                  <DevBaseCatalogPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/reconciliation"
              element={
                <OpsRoute>
                  <OpsReconciliationPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/audit"
              element={
                <OpsRoute>
                  <OpsAuditPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/health"
              element={
                <OpsRoute>
                  <OpsHealthPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/fiscal/providers"
              element={
                <OpsRoute>
                  <OpsFiscalProvidersPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/partners/dashboard"
              element={
                <OpsRoute>
                  <OpsPartnersDashboardPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/logistics/dashboard"
              element={
                <OpsRoute>
                  <OpsLogisticsDashboardPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/logistics/manifests"
              element={
                <OpsRoute>
                  <OpsLogisticsManifestsPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/logistics/manifests-overview"
              element={
                <OpsRoute>
                  <OpsLogisticsManifestsOverviewPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/logistics/returns"
              element={
                <OpsRoute>
                  <OpsLogisticsReturnsPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/products/catalog"
              element={
                <OpsRoute>
                  <OpsProductsCatalogPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/products/assets"
              element={
                <OpsRoute>
                  <OpsProductsAssetsPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/products/pricing-fiscal"
              element={
                <OpsRoute>
                  <OpsProductsPricingFiscalPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/products/inventory-health"
              element={
                <OpsRoute>
                  <OpsProductsInventoryHealthPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/integration/outbox-replay"
              element={
                <OpsRoute>
                  <OpsIntegrationOutboxReplayPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/integration/orders-fiscal"
              element={
                <OpsRoute>
                  <OpsIntegrationOrdersFiscalPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/integration/orders-partner-lookup"
              element={
                <OpsRoute>
                  <OpsIntegrationOrdersPartnerLookupPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/partners/financials-service-areas"
              element={
                <OpsRoute>
                  <OpsPartnersFinancialsServiceAreasPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/partners/reconciliation-dashboard"
              element={
                <OpsRoute>
                  <OpsPartnersReconciliationDashboardPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/partners/billing-monitor"
              element={
                <OpsRoute>
                  <OpsPartnersBillingMonitoringPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/partners/hypertables"
              element={
                <OpsRoute>
                  <OpsPartnersHypertablesPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/updates"
              element={
                <OpsRoute>
                  <OpsUpdatesHistoryPage />
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
              path="/ops/auth/policy"
              element={
                <OpsRoute>
                  <OpsAuthorizationPolicyPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/auth/policy/versioning"
              element={
                <OpsRoute>
                  <OpsVersioningPolicyPage />
                </OpsRoute>
              }
            />

            {/* Rota 404 - Página não encontrada */}
            <Route 
              path="*" 
              element={<PublicNotFoundPage />}
            />
          </Routes>
        </Suspense>
      </div>
      {/* <footer className="app-footer" role="contentinfo">
        <p>&copy; {new Date().getFullYear()} ELLAN Lab Locker. Todos os direitos reservados.</p>
      </footer> */}



      {/* <footer className="app-footer" role="contentinfo">
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', // Centraliza horizontalmente
          flexWrap: 'wrap', 
          gap: 'var(--spacing-2)',
          textAlign: 'center'
        }}>
          <p style={{ margin: 0 }}>
            &copy; {new Date().getFullYear()} ELLAN Lab Locker. Todos os direitos reservados.
          </p>
          <span aria-hidden="true">|</span>
          <Link 
            to="/suporte" 
            style={{ 
              textDecoration: 'none',
              color: 'inherit',
              transition: 'color var(--transition-base)'
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#667eea'}
            onMouseLeave={(e) => e.currentTarget.style.color = 'inherit'}
          >
            Central de Suporte
          </Link>
        </div>
      </footer> */}


      <footer className="app-footer" role="contentinfo">
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          flexWrap: 'wrap', 
          gap: 'var(--spacing-2)',
          textAlign: 'center'
        }}>
          <p style={{ margin: 0 }}>
            &copy; {new Date().getFullYear()} ELLAN Lab Locker. Todos os direitos reservados.
          </p>
          <span aria-hidden="true">|</span>
          <Link 
            to="/privacidade" 
            style={{ 
              textDecoration: 'none',
              color: 'inherit',
              transition: 'color var(--transition-base)'
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#667eea'}
            onMouseLeave={(e) => e.currentTarget.style.color = 'inherit'}
          >
            Política de Privacidade
          </Link>
          <span aria-hidden="true">|</span>
          <Link 
            to="/termos" 
            style={{ 
              textDecoration: 'none',
              color: 'inherit',
              transition: 'color var(--transition-base)'
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#667eea'}
            onMouseLeave={(e) => e.currentTarget.style.color = 'inherit'}
          >
            Termos de Uso
          </Link>
          <span aria-hidden="true">|</span>
          <Link 
            to="/suporte" 
            style={{ 
              textDecoration: 'none',
              color: 'inherit',
              transition: 'color var(--transition-base)'
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#667eea'}
            onMouseLeave={(e) => e.currentTarget.style.color = 'inherit'}
          >
            Central de Suporte
          </Link>
        </div>
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
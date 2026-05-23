
// 01_source/frontend/src/App.jsx
import React, { Suspense, lazy, useState, useEffect, useRef } from "react";
import { Routes, Route, Navigate, Link, useLocation, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import InteligenciaMenu from "./components/intelligence/InteligenciaMenu";
import { mlIntelligenceApi } from "./api/mlIntelligenceClient";
import FiscalPageLayout from "./components/FiscalPageLayout";
import DomainErrorBoundary from "./components/DomainErrorBoundary.tsx";
import { reportUiErrorTelemetry } from "./services/errorTelemetry.ts";
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
const PublicLegalPrivacyDocumentPage = lazy(() => import("./pages/public/PublicLegalPrivacyDocumentPage"));
const PublicLegalPrivacyIndexPage = lazy(() =>
  import("./pages/public/PublicLegalPrivacyDocumentPage").then((m) => ({ default: m.PublicLegalPrivacyIndexPage })),
);
const PublicPlayerLegalPrivacyDocumentPage = lazy(() =>
  import("./pages/public/PublicPlayerLegalPrivacyDocumentPage"),
);
const PublicPlayerLegalPrivacyIndexPage = lazy(() =>
  import("./pages/public/PublicPlayerLegalPrivacyDocumentPage").then((m) => ({
    default: m.PublicPlayerLegalPrivacyIndexPage,
  })),
);
const PublicTermsOfUsePage = lazy(() => import("./pages/public/PublicTermsOfUsePage"));
const PublicAccessDeniedPage = lazy(() => import("./pages/public/PublicAccessDeniedPage"));
const LockerDashboard = lazy(() => import("./pages/LockerDashboard"));
const OpsDiscontinuedEllanLabPage = lazy(() => import("./pages/OpsDiscontinuedEllanLabPage"));
const RegionPage = lazy(() => import("./pages/RegionPage"));
const DevLockerResetPage = lazy(() => import("./pages/DevLockerResetPage"));
const DevSlotAllocationPage = lazy(() => import("./pages/DevSlotAllocationPage"));
const DevBaseCatalogPage = lazy(() => import("./pages/DevBaseCatalogPage"));
const OrderPickupExecutiveSummaryPage = lazy(() => import("./pages/OrderPickupExecutiveSummaryPage"));
const OrderPickupHealthPage = lazy(() => import("./pages/OrderPickupHealthPage"));
const OrderDomainEventsPage = lazy(() => import("./pages/OrderDomainEventsPage"));
const OrderDeadlinesPage = lazy(() => import("./pages/OrderDeadlinesPage"));
const OpsAuthorizationPolicyPage = lazy(() => import("./pages/OpsAuthorizationPolicyPage"));
const OpsVersioningPolicyPage = lazy(() => import("./pages/OpsVersioningPolicyPage"));
const OpsReconciliationPage = lazy(() => import("./pages/OpsReconciliationPage"));
const PaymentReconciliationPage = lazy(() => import("./pages/PaymentReconciliationPage"));
const OpsHealthPage = lazy(() => import("./pages/OpsHealthPage"));
const OpsRuntimeHealthPage = lazy(() => import("./pages/OpsRuntimeHealthPage"));
const OpsRuntimeEventLogPage = lazy(() => import("./pages/OpsRuntimeEventLogPage"));
const OpsRuntimeSlotsMonitorPage = lazy(() => import("./pages/OpsRuntimeSlotsMonitorPage"));
const OpsRuntimeSyncPage = lazy(() => import("./pages/OpsRuntimeSyncPage"));
const OpsQuickEnablementPage = lazy(() => import("./pages/OpsQuickEnablementPage"));
const OpsKioskTouchModelsPage = lazy(() => import("./pages/OpsKioskTouchModelsPage"));
const OpsAuditPage = lazy(() => import("./pages/OpsAuditPage"));
const OpsNotificationLogsPage = lazy(() => import("./pages/OpsNotificationLogsPage"));
const OpsDevErrorsPage = lazy(() => import("./pages/OpsDevErrorsPage.tsx"));
const OpsFiscalProvidersPage = lazy(() => import("./pages/OpsFiscalProvidersPage"));
const OpsPartnersDashboardPage = lazy(() => import("./pages/OpsPartnersDashboardPage"));
const OpsLogisticsDashboardPage = lazy(() => import("./pages/OpsLogisticsDashboardPage"));
const OpsLogisticsReturnsPage = lazy(() => import("./pages/OpsLogisticsReturnsPage"));
const OpsReturnTrackingPage = lazy(() => import("./pages/OpsReturnTrackingPage"));
const OpsLogisticsManifestsPage = lazy(() => import("./pages/OpsLogisticsManifestsPage"));
const OpsLogisticsManifestsOverviewPage = lazy(() => import("./pages/OpsLogisticsManifestsOverviewPage"));
const OpsLogisticsInventoryPage = lazy(() => import("./pages/OpsLogisticsInventoryPage"));
const OpsUpdatesHistoryPage = lazy(() => import("./pages/OpsUpdatesHistoryPage"));
const OpsProductsCatalogPage = lazy(() => import("./pages/OpsProductsCatalogPage"));
const OpsProductsAssetsPage = lazy(() => import("./pages/OpsProductsAssetsPage"));
const OpsProductsPricingFiscalPage = lazy(() => import("./pages/OpsProductsPricingFiscalPage"));
const OpsPricingRulesPage = lazy(() => import("./pages/OpsPricingRulesPage"));
const OpsProductsInventoryHealthPage = lazy(() => import("./pages/OpsProductsInventoryHealthPage"));
const OpsProductCategoriesPage = lazy(() => import("./pages/OpsProductCategoriesPage"));
const OpsProductsProfessionalPage = lazy(() => import("./pages/OpsProductsProfessionalPage"));
const OpsProductsEcosystemPage = lazy(() => import("./pages/OpsProductsEcosystemPage"));
const OpsLockerProductConfigPage = lazy(() => import("./pages/OpsLockerProductConfigPage"));
const OpsLockerSlotsPage = lazy(() => import("./pages/OpsLockerSlotsPage"));
const OpsLockerOccupancyForecastPage = lazy(() => import("./pages/OpsLockerOccupancyForecastPage"));
const OpsLockerOperatorsPage = lazy(() => import("./pages/OpsLockerOperatorsPage"));
const OpsLockerCreatePage = lazy(() => import("./pages/OpsLockerCreatePage"));
const OpsPartnersAdminPage = lazy(() => import("./pages/OpsPartnersAdminPage"));
const OpsUserRolesPage = lazy(() => import("./pages/OpsUserRolesPage"));
const OpsTenantsAdminPage = lazy(() => import("./pages/OpsTenantsAdminPage"));
const OpsPaymentGatewayAdminPage = lazy(() => import("./pages/OpsPaymentGatewayAdminPage"));
const OpsOrderPickupAdminPage = lazy(() => import("./pages/OpsOrderPickupAdminPage"));
const OpsMarketplaceAdminPage = lazy(() => import("./pages/OpsMarketplaceAdminPage"));
const OpsFinanceAdminPage = lazy(() => import("./pages/OpsFinanceAdminPage"));
const OpsPrivacyComplianceAdminPage = lazy(() => import("./pages/OpsPrivacyComplianceAdminPage"));
const OpsMlAdminPage = lazy(() => import("./pages/OpsMlAdminPage"));
const OpsRentalContractsPage = lazy(() => import("./pages/OpsRentalContractsPage"));
const OpsRentalPlansPage = lazy(() => import("./pages/OpsRentalPlansPage"));
const OpsRentalAdminPage = lazy(() => import("./pages/OpsRentalAdminPage"));
const OpsProductBundlesPage = lazy(() => import("./pages/OpsProductBundlesPage"));
const OpsProductsAdminRedirect = lazy(() => import("./pages/OpsProductsAdminRedirect"));
const OpsPromotionsPage = lazy(() => import("./pages/OpsPromotionsPage"));
const OpsPromotionsAdminPage = lazy(() => import("./pages/OpsPromotionsAdminPage"));
const OpsIntegrationOutboxReplayPage = lazy(() => import("./pages/OpsIntegrationOutboxReplayPage"));
const OpsIntegrationOrdersFiscalPage = lazy(() => import("./pages/OpsIntegrationOrdersFiscalPage"));
const OpsIntegrationOrdersPartnerLookupPage = lazy(() => import("./pages/OpsIntegrationOrdersPartnerLookupPage"));
const OpsPartnersFinancialsServiceAreasPage = lazy(() => import("./pages/OpsPartnersFinancialsServiceAreasPage"));
const OpsPartnersReconciliationDashboardPage = lazy(() => import("./pages/OpsPartnersReconciliationDashboardPage"));
const OpsPartnersBillingMonitoringPage = lazy(() => import("./pages/OpsPartnersBillingMonitoringPage"));
const BillingInvoiceSearchPage = lazy(() => import("./pages/BillingInvoiceSearchPage"));
const BillingInvoiceQueuePage = lazy(() => import("./pages/BillingInvoiceQueuePage"));
const BillingReconciliationGapsPage = lazy(() => import("./pages/BillingReconciliationGapsPage"));
const BillingKpiDailyPage = lazy(() => import("./pages/BillingKpiDailyPage"));
const OpsPartnersHypertablesPage = lazy(() => import("./pages/OpsPartnersHypertablesPage"));
const OpsIntelligencePage = lazy(() => import("./pages/OpsIntelligencePage"));
const InteligenciaDashboardPage = lazy(() =>
  import("./pages/intelligence/views").then((m) => ({ default: m.InteligenciaDashboardPage }))
);
const ModelMonitorPage = lazy(() =>
  import("./pages/intelligence/views").then((m) => ({ default: m.ModelMonitorPage }))
);
const AtRiskLockersPage = lazy(() =>
  import("./pages/intelligence/views").then((m) => ({ default: m.AtRiskLockersPage }))
);
const PredictionHistoryPage = lazy(() =>
  import("./pages/intelligence/views").then((m) => ({ default: m.PredictionHistoryPage }))
);
const PartnerChurnPage = lazy(() =>
  import("./pages/intelligence/views").then((m) => ({ default: m.PartnerChurnPage }))
);
const CustomerLTVScoresPage = lazy(() =>
  import("./pages/intelligence/views").then((m) => ({ default: m.CustomerLTVScoresPage }))
);
const DynamicPricingPage = lazy(() =>
  import("./pages/intelligence/views").then((m) => ({ default: m.DynamicPricingPage }))
);
const PickupFraudDashboardPage = lazy(() =>
  import("./pages/intelligence/views").then((m) => ({ default: m.PickupFraudDashboardPage }))
);
const FeedbackNlpDashboardPage = lazy(() =>
  import("./pages/intelligence/views").then((m) => ({ default: m.FeedbackNlpDashboardPage }))
);
const OccupancyForecastIntelPage = lazy(() => import("./pages/OpsLockerOccupancyForecastPage"));
const RouteOptimizePage = lazy(() => import("./pages/RouteOptimizePage"));
const PartnerSettlementPage = lazy(() => import("./pages/PartnerSettlementPage"));
const FiscalGlobalPage = lazy(() => import("./pages/FiscalGlobalPage"));
const FiscalCountriesPage = lazy(() => import("./pages/FiscalCountriesPage"));
const FiscalUpdatesPage = lazy(() => import("./pages/FiscalUpdatesPage"));
const FiscalFg1GatePage = lazy(() => import("./pages/FiscalFg1GatePage"));
const FiscalReadinessExecutionPage = lazy(() => import("./pages/FiscalReadinessExecutionPage"));
const FiscalManagementDailyPage = lazy(() => import("./pages/FiscalManagementDailyPage"));
const FiscalDepartmentDashboardsPage = lazy(() => import("./pages/FiscalDepartmentDashboardsPage"));
const FiscalPartnerPerformancePage = lazy(() => import("./pages/FiscalPartnerPerformancePage"));
const FiscalAccountingClosePage = lazy(() => import("./pages/FiscalAccountingClosePage"));
const FiscalSloAlertsPage = lazy(() => import("./pages/FiscalSloAlertsPage"));
const FiscalSprint4RegressionMatrixPage = lazy(() => import("./pages/FiscalSprint4RegressionMatrixPage"));
const FiscalSprint2FinanceGatePage = lazy(() => import("./pages/FiscalSprint2FinanceGatePage"));
const FiscalSprint3PartnerAuditPage = lazy(() => import("./pages/FiscalSprint3PartnerAuditPage"));
const FiscalIncidentResponsePage = lazy(() => import("./pages/FiscalIncidentResponsePage"));

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

function normalizeRoleName(roleName) {
  return String(roleName || "")
    .trim()
    .toLowerCase()
    .replace(/[._\-\s]+/g, "_");
}

function hasAnyRole(hasRoleFn, roleNames) {
  return roleNames.some((roleName) => {
    const raw = String(roleName || "").trim().toLowerCase();
    const normalized = normalizeRoleName(roleName);
    return hasRoleFn(raw) || (normalized !== raw && hasRoleFn(normalized));
  });
}

function TopNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout, loading, hasRole } = useAuth();
  const fullName = user?.full_name || user?.email || "";
  const initials = initialsFromName(fullName);
  const opsEnabled = isOpsEnabled();
  const canAccessOps = isAuthenticated && hasAnyRole(hasRole, ["admin.operacao", "suporte", "auditoria"]);
  const canAccessIntelligence =
    isAuthenticated && hasAnyRole(hasRole, ["admin.operacao", "admin.financeiro"]);
  const canAccessBackofficeMenus = isAuthenticated && (canAccessOps || canAccessIntelligence);

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isOpsMenuOpen, setIsOpsMenuOpen] = useState(false);
  const [isIntelMenuOpen, setIsIntelMenuOpen] = useState(false);
  const [isFiscalMenuOpen, setIsFiscalMenuOpen] = useState(false);
  const [isMyAreaMenuOpen, setIsMyAreaMenuOpen] = useState(false);
  const [isMobileOpsOpen, setIsMobileOpsOpen] = useState(false);
  const [isMobileFiscalOpen, setIsMobileFiscalOpen] = useState(false);
  const [isMobileIntelOpen, setIsMobileIntelOpen] = useState(false);
  const [isMobileMyAreaOpen, setIsMobileMyAreaOpen] = useState(false);
  const [intelAtRiskBadge, setIntelAtRiskBadge] = useState(0);
  const [isMobile, setIsMobile] = useState(false);
  const [tenantOverride, setTenantOverride] = useState("");
  const menuRef = useRef(null);
  const buttonRef = useRef(null);
  const opsMenuRef = useRef(null);
  const opsButtonRef = useRef(null);
  const fiscalMenuRef = useRef(null);
  const fiscalButtonRef = useRef(null);
  const intelMenuRef = useRef(null);
  const intelButtonRef = useRef(null);
  const myAreaMenuRef = useRef(null);
  const myAreaButtonRef = useRef(null);
  const envTenant = String(import.meta.env.VITE_GEO_SCOPE_TENANT || "").trim().toUpperCase();
  const hasTenantOverride = Boolean(tenantOverride);
  const isOpsRoute = location.pathname.startsWith("/ops");
  const isFiscalRoute = location.pathname.startsWith("/fiscal");
  const isIntelligenceRoute = location.pathname.startsWith("/intelligence");

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
    const handleFiscalClickOutside = (event) => {
      if (
        isFiscalMenuOpen &&
        fiscalMenuRef.current &&
        !fiscalMenuRef.current.contains(event.target) &&
        fiscalButtonRef.current &&
        !fiscalButtonRef.current.contains(event.target)
      ) {
        setIsFiscalMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handleFiscalClickOutside);
    return () => document.removeEventListener("mousedown", handleFiscalClickOutside);
  }, [isFiscalMenuOpen]);

  useEffect(() => {
    const handleIntelClickOutside = (event) => {
      if (
        isIntelMenuOpen &&
        intelMenuRef.current &&
        !intelMenuRef.current.contains(event.target) &&
        intelButtonRef.current &&
        !intelButtonRef.current.contains(event.target)
      ) {
        setIsIntelMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleIntelClickOutside);
    return () => document.removeEventListener("mousedown", handleIntelClickOutside);
  }, [isIntelMenuOpen]);

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
    if (location.pathname.startsWith("/intelligence")) {
      return "linear-gradient(90deg, #0f172a 0%, #1e1b2e 100%)";
    }
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
    setIsIntelMenuOpen(false);
    setIsFiscalMenuOpen(false);
    setIsMyAreaMenuOpen(false);
    setIsMobileOpsOpen(false);
    setIsMobileIntelOpen(false);
    setIsMobileFiscalOpen(false);
    setIsMobileMyAreaOpen(false);
  }, [location]);

  useEffect(() => {
    if (!opsEnabled || !canAccessIntelligence) {
      setIntelAtRiskBadge(0);
      return;
    }
    mlIntelligenceApi
      .dashboard()
      .then((d) => setIntelAtRiskBadge(Number(d.at_risk_count) || 0))
      .catch(() => setIntelAtRiskBadge(0));
  }, [opsEnabled, canAccessIntelligence, location.pathname]);

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
    {
      to: "/ops/kiosk-touch-models",
      label: "ops /kiosk-touch-models",
      aria: "Protótipos navegáveis KIOSK touch v1 (Sprint 1)",
      group: "Visão Geral",
    },
    { to: "/ops/health", label: "ops /health", aria: "Saúde operacional e alertas", group: "Dashboards" },
    { to: "/ops/runtime/health", label: "ops /runtime/health", aria: "Health do backend runtime (8200)", group: "Runtime" },
    { to: "/ops/runtime/events", label: "ops /runtime/events", aria: "Log de eventos SQLite do runtime", group: "Runtime" },
    { to: "/ops/runtime/slots", label: "ops /runtime/slots", aria: "Monitor de slots do locker runtime", group: "Runtime" },
    {
      to: "/ops/runtime/sync",
      label: "ops /runtime/sync",
      aria: "Reconciliação locker_slots (Postgres) com runtime",
      group: "Runtime",
    },
    {
      to: "/ops/quick-enablement",
      label: "ops /quick-enablement",
      aria: "Treinamento rapido OPS e Suporte (Sprint 3)",
      group: "Dashboards",
    },
    { to: "/ops/audit", label: "ops /audit", aria: "Trilha de auditoria operacional", group: "Dashboards" },
    {
      to: "/ops/notifications/logs",
      label: "ops /notifications/logs",
      aria: "Logs de notificação (email/sms/push) e reenvio",
      group: "Dashboards",
    },
    { to: "/ops/dev/errors", label: "ops /dev/errors", aria: "Visualizacao interna de erros 4xx/5xx", group: "Dashboards" },
    { to: "/ops/reconciliation", label: "ops /reconciliation", aria: "Reconciliação operacional por order_id", group: "Dashboards" },
    { to: "/ops/updates", label: "ops /updates", aria: "Historico de acrescimos operacionais", group: "Dashboards" },
    {
      to: "/ops/access/user-roles",
      label: "Papeis de acesso (user_roles)",
      aria: "Gerenciar tabela user_roles e associacoes",
      group: "Cadastros OPS",
      opsSubGroup: "Acesso",
    },
    {
      to: "/ops/payment-gateway/admin",
      label: "Payment Gateway — catalogo e PSP",
      aria: "Metodos de pagamento, PSP, webhook, API key, device registry e risk",
      group: "Cadastros OPS",
      opsSubGroup: "Payment Gateway",
    },
    {
      to: "/ops/finance/admin?tab=networks",
      label: "Finance — redes mundiais",
      aria: "Catálogo 88+ players: InPost, DHL, Magalu, Mercado Livre, Amazon, carriers, food delivery",
      group: "Finance OPS — Global",
      opsSubGroup: "Catálogo",
      newTag: "Global",
    },
    {
      to: "/ops/finance/admin?tab=ecosystem",
      label: "Finance — ecossistema",
      aria: "KPIs globais, relações entre players, cobertura de capacidades",
      group: "Finance OPS — Global",
      opsSubGroup: "Inteligência",
      newTag: "KPI",
    },
    {
      to: "/ops/finance/admin?tab=readiness",
      label: "Finance — readiness",
      aria: "Score de prontidão financeira por player do catálogo (grade A–D)",
      group: "Finance OPS — Global",
      opsSubGroup: "Inteligência",
    },
    {
      to: "/ops/finance/admin?tab=roadmap",
      label: "Finance — roadmap",
      aria: "Marcos de integração DISCOVERY PILOT UAT LIVE",
      group: "Finance OPS — Global",
      opsSubGroup: "Inteligência",
    },
    {
      to: "/ops/finance/admin?tab=contracts",
      label: "Finance — contratos",
      aria: "MSA e contratos comerciais por parceiro",
      group: "Finance OPS — Global",
      opsSubGroup: "Inteligência",
    },
    {
      to: "/ops/finance/admin?tab=slas",
      label: "Finance — SLAs",
      aria: "Definições de SLA e breaches com crédito automático",
      group: "Finance OPS — Global",
      opsSubGroup: "Inteligência",
    },
    {
      to: "/ops/finance/admin?tab=dunning",
      label: "Finance — cobranca",
      aria: "Dunning B2B: faturas vencidas e estagios de cobranca",
      group: "Finance OPS — Comercial",
      opsSubGroup: "Cobranca",
    },
    {
      to: "/ops/finance/admin?tab=tiers",
      label: "Finance — niveis",
      aria: "Tiers comerciais STANDARD GROWTH ENTERPRISE",
      group: "Finance OPS — Comercial",
      opsSubGroup: "Tiers",
    },
    {
      to: "/ops/finance/admin?tab=fx",
      label: "Finance — cambio",
      aria: "Taxas FX para settlement multi-moeda",
      group: "Finance OPS — Comercial",
      opsSubGroup: "FX",
    },
    {
      to: "/ops/finance/admin?tab=tax",
      label: "Finance — corredores fiscais",
      aria: "Regimes fiscais por corridor BR PT ES",
      group: "Finance OPS — Comercial",
      opsSubGroup: "Fiscal",
    },
    {
      to: "/ops/finance/admin?tab=documents",
      label: "Finance — docs NF",
      aria: "PDF XML access_key vinculados a NF B2B",
      group: "Finance OPS — Comercial",
      opsSubGroup: "Documentos",
    },
    {
      to: "/ops/finance/admin?tab=audit",
      label: "Finance — auditoria",
      aria: "Trilha imutavel de acoes financeiras",
      group: "Finance OPS — Comercial",
      opsSubGroup: "Auditoria",
    },
    {
      to: "/ops/finance/admin?tab=revrec",
      label: "Finance — rev. receita",
      aria: "Schedules de diferimento STRAIGHT_LINE e sync fiscal",
      group: "Finance OPS — Comercial",
      opsSubGroup: "RevRec",
    },
    {
      to: "/ops/finance/admin?tab=jobs",
      label: "Finance — jobs",
      aria: "Dunning, reconciliacao, revrec e fiscal gap sync agendados",
      group: "Finance OPS — Comercial",
      opsSubGroup: "Jobs",
    },
    {
      to: "/ops/finance/admin",
      label: "Finance — visao geral",
      aria: "Parceiros financeiros, billing B2B, wallet, NF ops e eventos",
      group: "Finance OPS",
      opsSubGroup: "Visao geral",
      newTag: "Hub",
    },
    {
      to: "/ops/finance/admin?tab=partners",
      label: "Finance — parceiros",
      aria: "finance_partner_accounts, webhook e API keys",
      group: "Finance OPS",
      opsSubGroup: "Parceiros",
    },
    {
      to: "/ops/finance/admin?tab=billing",
      label: "Finance — planos e ciclos",
      aria: "partner_billing_plans e partner_billing_cycles",
      group: "Finance OPS",
      opsSubGroup: "Billing",
    },
    {
      to: "/ops/finance/admin?tab=invoices",
      label: "Finance — NF B2B",
      aria: "partner_b2b_invoices",
      group: "Finance OPS",
      opsSubGroup: "NF B2B",
    },
    {
      to: "/ops/finance/admin?tab=wallet",
      label: "Finance — wallet",
      aria: "wallet_provider_catalog e wallet_transactions",
      group: "Finance OPS",
      opsSubGroup: "Wallet",
    },
    {
      to: "/ops/finance/admin?tab=settlements",
      label: "Finance — settlements",
      aria: "partner_settlement_batches e itens",
      group: "Finance OPS",
      opsSubGroup: "Settlements",
    },
    {
      to: "/ops/finance/admin?tab=treasury",
      label: "Finance — treasury",
      aria: "credit_notes, payment_holds, commission_structure",
      group: "Finance OPS",
      opsSubGroup: "Treasury",
    },
    {
      to: "/ops/finance/admin?tab=pnl",
      label: "Finance — PnL locker",
      aria: "cost_centers e cost_center_monthly",
      group: "Finance OPS",
      opsSubGroup: "PnL",
    },
    {
      to: "/ops/finance/admin?tab=reconciliation",
      label: "Finance — gaps fiscais",
      aria: "fiscal_reconciliation_gaps",
      group: "Finance OPS",
      opsSubGroup: "Reconciliacao",
    },
    {
      to: "/ops/finance/admin?tab=webhooks",
      label: "Finance — webhook DLQ",
      aria: "partner_webhook_deliveries falhas",
      group: "Finance OPS",
      opsSubGroup: "Webhooks",
    },
    {
      to: "/ops/finance/admin?tab=ops",
      label: "Finance — fiscal ops",
      aria: "finance_ops_invoices e billing_processed_events",
      group: "Finance OPS",
      opsSubGroup: "Fiscal ops",
    },
    {
      to: "/ops/order-pickup/admin",
      label: "Order Pickup — pedidos e integracao",
      aria: "Parceiros pickup, pedidos, outbox, credits e fulfillment",
      group: "Cadastros OPS",
      opsSubGroup: "Order Pickup",
    },
    {
      to: "/ops/marketplace/admin",
      label: "Marketplace — visao geral",
      aria: "Dashboard KPIs, sellers, catalogo, comissoes, repasses, KYC e disputas",
      group: "Marketplace OPS",
      opsSubGroup: "Visao geral",
    },
    {
      to: "/ops/marketplace/admin?tab=settlements",
      label: "Marketplace — repasses",
      aria: "Lotes de liquidacao ao seller e contas PIX",
      group: "Marketplace OPS",
      opsSubGroup: "Financeiro",
    },
    {
      to: "/ops/marketplace/admin?tab=kyc",
      label: "Marketplace — KYC / compliance",
      aria: "Documentos de onboarding e aprovacao de sellers",
      group: "Marketplace OPS",
      opsSubGroup: "Compliance",
    },
    {
      to: "/ops/marketplace/admin?tab=channels",
      label: "Marketplace — canais e redes locker",
      aria: "InPost, DHL, Magalu, Mercado Livre, Amazon, DPD, Correios, CTT e vinculos seller",
      group: "Marketplace OPS",
      opsSubGroup: "Canais",
    },
    {
      to: "/ops/marketplace/admin?tab=readiness",
      label: "Marketplace — prontidao integracao",
      aria: "Score GO_LIVE/PILOT, incidentes e auditoria de sync",
      group: "Marketplace OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/ops/marketplace/admin?tab=readiness",
      label: "Marketplace — Global OPS (corredores · SLA)",
      aria: "Certificacoes, corredores internacionais e espelho partner",
      group: "Marketplace OPS",
      opsSubGroup: "Global OPS",
      newTag: "New1",
    },
    {
      to: "/ops/privacy-compliance/admin",
      label: "Privacy — visao geral (compliance global)",
      aria: "Dashboard KPIs privacy, marcos regulatorios e politicas",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Visao geral",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=compliance",
      label: "Privacy — score compliance",
      aria: "Nota A-F, gaps e comparativo GDPR/LGPD/CCPA",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Score",
      newTag: "New",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=regulation_hub",
      label: "Privacy — hub GDPR / LGPD / CCPA",
      aria: "Visao 360 por marco regulatorio em foco",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Hub marco",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=regulatory_toolkit",
      label: "Privacy — toolkit GDPR / LGPD / CCPA",
      aria: "Direitos titular, obrigacoes, LIA, opt-out CCPA/GPC e templates autoridade",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Hub marco",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=regulations",
      label: "Privacy — marcos regulatorios",
      aria: "CRUD marcos GDPR, LGPD, CCPA e 15+ jurisdicoes",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Catalogo",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=policies",
      label: "Privacy — politicas de privacidade",
      aria: "Versoes vigentes e historicas por marco",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Catalogo",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=legal_bases",
      label: "Privacy — bases legais",
      aria: "Art. 6 GDPR, bases LGPD e opt-out CCPA",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Catalogo",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=data_categories",
      label: "Privacy — categorias de dados",
      aria: "Inventario de categorias e sensibilidade",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Catalogo",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=ropa",
      label: "Privacy — ROPA (tratamentos + grafo)",
      aria: "Registro Art. 30 GDPR e mapa React Flow",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "ROPA",
      newTag: "New",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=processors",
      label: "Privacy — processadores e DPA",
      aria: "Subprocessadores, redes locker e acordos DPA/SCC",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Processadores",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=retention",
      label: "Privacy — retencao",
      aria: "Regras de retencao e purge por categoria",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Processadores",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=consents",
      label: "Privacy — consentimentos",
      aria: "Registro, analytics e revogacao por canal",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Titulares",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=deletions",
      label: "Privacy — eliminacao de dados",
      aria: "Pedidos de exclusao (right to erasure)",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Titulares",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=subject_requests",
      label: "Privacy — DSAR titulares",
      aria: "Acesso, portabilidade, playbook automatizado",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Titulares",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=breaches",
      label: "Privacy — incidentes / violacoes",
      aria: "Timeline 72h GDPR/ANPD e notificacao titulares",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Incidentes",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=dpia",
      label: "Privacy — DPIA / LIA / PIA",
      aria: "Avaliacoes de impacto por marco regulatorio",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Incidentes",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=transfers",
      label: "Privacy — transferencias (wizard SCC/BCR)",
      aria: "Wizard step-by-step e registros cross-border",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Transferencias",
      newTag: "New",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=ecosystem",
      label: "Privacy — ecossistema locker mundial",
      aria: "77 players, relacoes, health probes e certificacoes Partner",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Ecossistema",
      newTag: "New",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=audit",
      label: "Privacy — trilha de auditoria",
      aria: "Eventos imutaveis DPO/regulador",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Auditoria",
      newTag: "New",
    },
    {
      to: "/ops/privacy-compliance/admin?tab=integrations",
      label: "Privacy — webhooks e entregas (DLQ)",
      aria: "Webhooks, dispatcher e fila privacy_webhook_deliveries",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/privacidade",
      label: "Privacy — pagina publica /privacidade",
      aria: "Politica resumida, seletor jurisdicao e redes locker",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Publico",
    },
    {
      to: "/legal/privacy/players",
      label: "Privacy — docs por player",
      aria: "Documentos legais Mercado Livre, InPost, DHL, Amazon Hub, iFood, etc.",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Publico",
    },
    {
      to: "/legal/privacy",
      label: "Privacy — documentos legais",
      aria: "Indice GDPR, LGPD, CCPA, UK, PT, ES, JP, SG por versao",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Publico",
    },
    {
      to: "/ops/ml/admin",
      label: "ML — visao geral",
      aria: "Dashboard KPIs ML, parceiros de dados, modelos e feedback",
      group: "ML OPS",
      opsSubGroup: "Visao geral",
    },
    {
      to: "/ops/ml/admin?tab=partners",
      label: "ML — parceiros de dados",
      aria: "CRUD parceiros ML, webhook e rotacao de API key",
      group: "ML OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/ops/ml/admin?tab=readiness",
      label: "ML — prontidao integracao",
      aria: "Score por rede locker, telemetria e perfis ML",
      group: "ML OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/ops/ml/admin?tab=networks",
      label: "ML — redes locker mundiais",
      aria: "InPost, DHL, Magalu, Mercado Livre, Amazon, DPD, Correios, CTT e perfis ML por rede",
      group: "ML OPS",
      opsSubGroup: "Redes",
    },
    {
      to: "/ops/ml/admin?tab=models",
      label: "ML — modelos",
      aria: "Versoes de modelo, metricas e status ACTIVE/STALE",
      group: "ML OPS",
      opsSubGroup: "Modelos",
    },
    {
      to: "/ops/ml/admin?tab=features",
      label: "ML — features diarias",
      aria: "Tabela ml_features_daily por locker e data",
      group: "ML OPS",
      opsSubGroup: "Dados",
    },
    {
      to: "/ops/ml/admin?tab=predictions",
      label: "ML — predicoes",
      aria: "Log ml_predictions_log e health score",
      group: "ML OPS",
      opsSubGroup: "Scoring",
    },
    {
      to: "/ops/ml/admin?tab=feedback",
      label: "ML — feedback",
      aria: "ml_prediction_feedback e validacao de drift",
      group: "ML OPS",
      opsSubGroup: "Qualidade",
    },
    {
      to: "/ops/ml/admin?tab=use_cases",
      label: "ML — casos de uso",
      aria: "Catalogo LOCKER_HEALTH, churn, fraud, LTV, pricing",
      group: "ML OPS",
      opsSubGroup: "Plataforma",
    },
    {
      to: "/ops/ml/admin?tab=registry",
      label: "ML — model registry",
      aria: "Versoes, stages DEV/STAGING/PRODUCTION e promote",
      group: "ML OPS",
      opsSubGroup: "Plataforma",
    },
    {
      to: "/ops/ml/admin?tab=training",
      label: "ML — experimentos",
      aria: "Training runs e metricas de treino",
      group: "ML OPS",
      opsSubGroup: "Plataforma",
    },
    {
      to: "/ops/ml/admin?tab=catalog",
      label: "ML — catalogo features",
      aria: "Definicoes de features e SLA de freshness",
      group: "ML OPS",
      opsSubGroup: "Dados",
    },
    {
      to: "/ops/ml/admin?tab=drift",
      label: "ML — drift",
      aria: "Relatorios PSI e status OK/WARNING/CRITICAL",
      group: "ML OPS",
      opsSubGroup: "Monitoramento",
    },
    {
      to: "/ops/ml/admin?tab=governance",
      label: "ML — SLO e alertas",
      aria: "SLO de inferencia e regras de alerta",
      group: "ML OPS",
      opsSubGroup: "Governanca",
    },
    {
      to: "/ops/ml/admin?tab=deployments",
      label: "ML — deployments",
      aria: "Trilha promote/rollback de modelos",
      group: "ML OPS",
      opsSubGroup: "Governanca",
    },
    {
      to: "/ops/order/executive-summary",
      label: "ops /order/executive-summary",
      aria: "Resumo executivo pickup (order lifecycle)",
      group: "Order / Pickup",
    },
    {
      to: "/ops/order/pickup-health",
      label: "ops /order/pickup-health",
      aria: "Saúde analytics pickup (order lifecycle)",
      group: "Order / Pickup",
    },
    {
      to: "/ops/intelligence",
      label: "ops /intelligence",
      aria: "Manutenção preditiva e ML (dashboard)",
      group: "Inteligência",
      opsSubGroup: "ML",
    },
    {
      to: "/ops/feedback-nlp",
      label: "ops /feedback-nlp",
      aria: "NPS, sentimentos e nuvem de palavras (customer_feedback + NLP)",
      group: "Inteligência",
      opsSubGroup: "ML",
    },
    {
      to: "/intelligence/ltv-scores",
      label: "intelligence /ltv-scores",
      aria: "LTV preditivo clientes (BG/NBD + Gamma-Gamma, campanhas)",
      group: "Inteligência",
      opsSubGroup: "ML",
    },
    {
      to: "/ops/order/domain-events",
      label: "ops /order/domain-events",
      aria: "Eventos de domínio pendentes (order lifecycle)",
      group: "Order / Pickup",
    },
    {
      to: "/ops/order/deadlines",
      label: "ops /order/deadlines",
      aria: "Deadlines lifecycle (documentação / gap listagem)",
      group: "Order / Pickup",
    },
    {
      to: "/ops/lockers/product-configs",
      label: "ops /lockers/product-configs",
      aria: "Regras product_locker_configs por locker (categoria permitida, dimensões, temperatura)",
      group: "Lockers",
      opsSubGroup: "Lockers",
    },
    {
      to: "/ops/lockers/create",
      label: "ops /lockers/create",
      aria: "Criar um ou varios lockers (CRUD, webhook, rotacao API key)",
      group: "Lockers",
      opsSubGroup: "Lockers",
    },
    {
      to: "/ops/lockers/slots",
      label: "ops /lockers/slots",
      aria: "Grade locker_slots + configs e force-release admin",
      group: "Lockers",
      opsSubGroup: "Lockers",
    },
    {
      to: "/ops/lockers/occupancy-forecast",
      label: "ops /lockers/occupancy-forecast",
      aria: "Heatmap de ocupação prevista (LSTM) + alertas",
      group: "Lockers",
      opsSubGroup: "Lockers",
    },
    {
      to: "/ops/lockers/operators",
      label: "ops /lockers/operators",
      aria: "CRUD locker_operators (comissao, contrato, status)",
      group: "Lockers",
      opsSubGroup: "Lockers",
    },
    {
      to: "/ops/rentals/admin",
      label: "ops /rentals/admin",
      aria: "Hub OPS rental — visão geral, seed, KPIs premium",
      group: "Rentals OPS",
      opsSubGroup: "Hub",
      newTag: "Hub",
    },
    {
      to: "/ops/rentals/admin?tab=networks",
      label: "ops /rentals/networks",
      aria: "Redes locker mundiais (InPost, DHL, Shopee…)",
      group: "Rentals OPS",
      opsSubGroup: "Redes",
    },
    {
      to: "/ops/rentals/admin?tab=corridors",
      label: "ops /rentals/corridors",
      aria: "Corredores logísticos internacionais",
      group: "Rentals OPS",
      opsSubGroup: "Redes",
    },
    {
      to: "/ops/rentals/admin?tab=onboarding",
      label: "ops /rentals/onboarding",
      aria: "KYB/KYC rental_network_onboarding",
      group: "Rentals OPS",
      opsSubGroup: "Premium",
      newTag: "KYB",
    },
    {
      to: "/ops/rentals/admin?tab=capacity",
      label: "ops /rentals/capacity",
      aria: "Utilização de slots rental_capacity_snapshots",
      group: "Rentals OPS",
      opsSubGroup: "Premium",
    },
    {
      to: "/ops/rentals/admin?tab=operators",
      label: "ops /rentals/operators",
      aria: "Operadores B2B e comissões",
      group: "Rentals OPS",
      opsSubGroup: "Operadores",
    },
    {
      to: "/ops/rentals/admin?tab=plans",
      label: "ops /rentals/plans (CRUD)",
      aria: "Planos rental_plans",
      group: "Rentals OPS",
      opsSubGroup: "Planos",
    },
    {
      to: "/ops/rentals/plans",
      label: "ops /rentals/plans (lista)",
      aria: "Listagem de planos ativos",
      group: "Rentals OPS",
      opsSubGroup: "Planos",
    },
    {
      to: "/ops/rentals/admin?tab=contracts",
      label: "ops /rentals/contracts (CRUD)",
      aria: "Contratos rental_contracts — preview-pricing e seguro de conteúdo",
      group: "Rentals OPS",
      opsSubGroup: "Contratos",
      newTag: "New",
    },
    {
      to: "/ops/rentals/admin?tab=contracts",
      label: "ops /rentals/preview-pricing",
      aria: "POST contracts/preview-pricing — cotação dinâmica (rental_pricing_rules)",
      group: "Rentals OPS",
      opsSubGroup: "Contratos",
      newTag: "New",
    },
    {
      to: "/ops/rentals/contracts",
      label: "ops /rentals/contracts (lista)",
      aria: "Listagem e detalhe de contratos",
      group: "Rentals OPS",
      opsSubGroup: "Contratos",
    },
    {
      to: "/ops/rentals/admin?tab=billing",
      label: "ops /rentals/billing",
      aria: "Faturamento rental_billing_invoices e multas automáticas (apply-late-fees)",
      group: "Rentals OPS",
      opsSubGroup: "Financeiro",
      newTag: "New",
    },
    {
      to: "/ops/rentals/admin?tab=billing",
      label: "ops /rentals/apply-late-fees",
      aria: "POST billing/apply-late-fees — rental_late_fee_policies",
      group: "Rentals OPS",
      opsSubGroup: "Financeiro",
      newTag: "New",
    },
    {
      to: "/ops/rentals/admin?tab=settlements",
      label: "ops /rentals/settlements",
      aria: "Liquidação operadores rental_settlement_batches",
      group: "Rentals OPS",
      opsSubGroup: "Financeiro",
      newTag: "New",
    },
    {
      to: "/ops/rentals/admin?tab=sla",
      label: "ops /rentals/sla",
      aria: "Políticas SLA por rede",
      group: "Rentals OPS",
      opsSubGroup: "Compliance",
    },
    {
      to: "/ops/rentals/admin?tab=premium",
      label: "ops /rentals/premium",
      aria: "Incidentes SLA, disputas e renovações",
      group: "Rentals OPS",
      opsSubGroup: "Compliance",
      newTag: "New",
    },
    {
      to: "/ops/rentals/admin?tab=events",
      label: "ops /rentals/events",
      aria: "Auditoria rental_contract_events",
      group: "Rentals OPS",
      opsSubGroup: "Auditoria",
    },
    {
      to: "/ops/rentals/admin?tab=integrations",
      label: "ops /rentals/integrations",
      aria: "Webhooks, entregas e API keys",
      group: "Rentals OPS",
      opsSubGroup: "Integrações",
    },
    {
      to: "/ops/rentals/admin?tab=advanced",
      label: "ops /rentals/advanced",
      aria: "Passes, cauções, pricing/quote, dunning, transferências, seguro de conteúdo",
      group: "Rentals OPS",
      opsSubGroup: "Avançado",
      newTag: "New",
    },
    {
      to: "/ops/rentals/admin?tab=advanced",
      label: "ops /rentals/content-insurance",
      aria: "GET content-insurance — apólices rental_content_insurance",
      group: "Rentals OPS",
      opsSubGroup: "Financeiro",
      newTag: "New",
    },
    {
      to: "/ops/payments/reconciliation",
      label: "ops /payments/reconciliation",
      aria: "Conciliação payment_transactions e payment_splits (status e lote)",
      group: "Order / Pickup",
    },
    { to: "/ops/logistics/dashboard", label: "ops /logistics/dashboard", aria: "Dashboard OPS de Logistics", group: "Logística" },
    { to: "/ops/logistics/manifests", label: "ops /logistics/manifests", aria: "Operacao OPS de manifestos L3/D2", group: "Logística" },
    { to: "/ops/logistics/manifests-overview", label: "ops /logistics/manifests-overview", aria: "Overview OPS de manifestos L3/D3", group: "Logística" },
    { to: "/ops/logistics/returns", label: "ops /logistics/returns", aria: "Dashboard OPS de Returns", group: "Logística" },
    { to: "/ops/returns/tracking", label: "ops /returns/tracking", aria: "Eventos de tracking por return leg", group: "Logística" },
    {
      to: "/ops/logistics/route-optimize",
      label: "ops /logistics/route-optimize",
      aria: "Roteirização ML com mapa (K-means + OR-Tools + RF)",
      group: "Logística",
    },
    {
      to: "/ops/logistics/inventory",
      label: "ops /logistics/inventory",
      aria: "Inventário OPS: estoque por SKU/locker e reservas",
      group: "Logística / Inventário",
    },
    {
      to: "/ops/products/ecosystem",
      label: "Ecossistema mundial",
      aria: "Players globais, elegibilidade categoria×rede e sync parceiros B2B",
      group: "Produtos & Catálogo",
      opsSubGroup: "Catálogo mundial",
      newTag: "Hub",
    },
    {
      to: "/ops/products/professional",
      label: "PIM — taxonomias e canais",
      aria: "Taxonomias GS1/ML/Amazon, listings de canal e atributos PIM",
      group: "Produtos & Catálogo",
      opsSubGroup: "Catálogo mundial",
    },
    {
      to: "/ops/products/catalog",
      label: "Catálogo SKU",
      aria: "Dashboard OPS de catálogo de produtos",
      group: "Produtos & Catálogo",
      opsSubGroup: "Catálogo operacional",
    },
    {
      to: "/ops/products/categories",
      label: "Categorias",
      aria: "CRUD de product_categories (árvore hierárquica)",
      group: "Produtos & Catálogo",
      opsSubGroup: "Catálogo operacional",
    },
    {
      to: "/ops/products/assets",
      label: "Mídia & barcodes",
      aria: "Mídia, EAN/GTIN e qualidade de dados de produto",
      group: "Produtos & Catálogo",
      opsSubGroup: "Catálogo operacional",
    },
    {
      to: "/ops/products/bundles",
      label: "Bundles",
      aria: "Kits e composições product_bundles",
      group: "Produtos & Catálogo",
      opsSubGroup: "Catálogo operacional",
    },
    {
      to: "/ops/products/pricing-fiscal",
      label: "Pricing & fiscal",
      aria: "Preços, impostos e alinhamento fiscal por SKU",
      group: "Produtos & Catálogo",
      opsSubGroup: "Comercial & estoque",
    },
    {
      to: "/ops/products/pricing-rules",
      label: "Regras de preço",
      aria: "pricing_rules por região, categoria e vigência",
      group: "Produtos & Catálogo",
      opsSubGroup: "Comercial & estoque",
    },
    {
      to: "/ops/products/inventory-health",
      label: "Saúde do estoque",
      aria: "Sinais de ruptura, reservas e inconsistências",
      group: "Produtos & Catálogo",
      opsSubGroup: "Comercial & estoque",
    },
    {
      to: "/ops/marketing/promotions",
      label: "Hub Promoções (mundial)",
      aria: "Overview, campanhas, promoções, escopos e resgates",
      group: "Marketing",
      opsSubGroup: "Campanhas",
      newTag: "Hub",
    },
    {
      to: "/ops/marketing/promotions?tab=campaigns",
      label: "Campanhas",
      aria: "promotion_campaigns por marketplace/carrier/rede locker",
      group: "Marketing",
      opsSubGroup: "Campanhas",
    },
    {
      to: "/ops/marketing/promotions?tab=redemptions",
      label: "Resgates",
      aria: "Trilha promotion_redemptions",
      group: "Marketing",
      opsSubGroup: "Campanhas",
    },
    {
      to: "/ops/marketing/promotions?tab=promotions",
      label: "Promoções (lista)",
      aria: "Listagem, escopos, exclusões e clonar",
      group: "Marketing",
      opsSubGroup: "Campanhas",
    },
    {
      to: "/ops/marketing/promotions?tab=lab",
      label: "Laboratório promo",
      aria: "Simular, match, conflitos e matriz player",
      group: "Marketing",
      opsSubGroup: "Campanhas",
      newTag: "Lab",
    },
    {
      to: "/ops/products/pricing-fiscal",
      label: "Pricing & fiscal — API lab",
      aria: "Overview PR3, bundles e validate promotion",
      group: "Marketing",
      opsSubGroup: "Campanhas",
    },
    {
      to: "/ops/products/bundles",
      label: "Bundles (PR3)",
      aria: "Kits e composições product_bundles",
      group: "Marketing",
      opsSubGroup: "Campanhas",
    },
    {
      to: "/ops/products/pricing-rules",
      label: "Regras de preço",
      aria: "pricing_rules por região, categoria e vigência",
      group: "Marketing",
      opsSubGroup: "Campanhas",
    },
    { to: "/ops/billing/invoices", label: "ops /billing/invoices", aria: "Busca de invoice (internal)", group: "Billing / Fiscal" },
    { to: "/ops/billing/invoice-queue", label: "ops /billing/invoice-queue", aria: "Fila operacional (dead letters + gaps)", group: "Billing / Fiscal" },
    { to: "/ops/billing/reconciliation-gaps", label: "ops /billing/reconciliation-gaps", aria: "Gaps de reconciliação fiscal", group: "Billing / Fiscal" },
    { to: "/ops/billing/kpis", label: "ops /billing/kpis", aria: "KPI financeiro diário (FA-5)", group: "Billing / Fiscal" },
    {
      to: "/ops/fiscal/providers",
      label: "Providers fiscais (BR/PT)",
      aria: "Status de providers fiscais por país",
      group: "Produtos & Catálogo",
      opsSubGroup: "Fiscal produto",
    },
    { to: "/ops/integration/outbox-replay", label: "ops /integration/outbox-replay", aria: "Operacao de replay em lote do outbox de integracao", group: "Integrações" },
    { to: "/ops/integration/orders-fiscal", label: "ops /integration/orders-fiscal", aria: "Operacao I-1 por order_id (fulfillment, events, fiscal)", group: "Integrações" },
    { to: "/ops/integration/orders-partner-lookup", label: "ops /integration/orders-partner-lookup", aria: "Operacao L-3 para lookup dedicado por partner/ref", group: "Integrações" },
    {
      to: "/ops/partners/admin",
      label: "Parceiros — cadastro e integracoes",
      aria: "CRUD parceiros, webhook, API keys, contatos e dominio",
      group: "Partners",
      opsSubGroup: "Cadastro",
      newTag: "New1",
    },
    {
      to: "/ops/partners/admin?tab=onboarding",
      label: "Parceiros — onboarding B2B",
      aria: "Checklist KYC até go-live",
      group: "Partners",
      opsSubGroup: "Cadastro",
      newTag: "New2",
    },
    {
      to: "/ops/partners/admin?tab=webhook_monitor",
      label: "Parceiros — entregas webhook",
      aria: "Monitor de partner_webhook_deliveries",
      group: "Partners",
      opsSubGroup: "Integração",
      newTag: "New3",
    },
    {
      to: "/ops/partners/admin?tab=integration_health",
      label: "Parceiros — saúde integração",
      aria: "Probes e histórico integration_health",
      group: "Partners",
      opsSubGroup: "Integração",
      newTag: "New4",
    },
    {
      to: "/ops/partners/admin?tab=outbox",
      label: "Parceiros — outbox eventos",
      aria: "Fila partner_order_events_outbox",
      group: "Partners",
      opsSubGroup: "Integração",
      newTag: "New5",
    },
    {
      to: "/ops/partners/admin?tab=settlements",
      label: "Parceiros — settlements (admin)",
      aria: "Aba settlements no admin unificado",
      group: "Partners",
      opsSubGroup: "Financeiro",
      newTag: "New6",
    },
    {
      to: "/ops/partners/admin?tab=invoices",
      label: "Parceiros — NF B2B",
      aria: "partner_b2b_invoices",
      group: "Partners",
      opsSubGroup: "Financeiro",
      newTag: "New7",
    },
    {
      to: "/ops/partners/admin?tab=credits",
      label: "Parceiros — créditos",
      aria: "partner_credit_notes",
      group: "Partners",
      opsSubGroup: "Financeiro",
      newTag: "New8",
    },
    {
      to: "/ops/partners/admin?tab=holds",
      label: "Parceiros — retenções",
      aria: "partner_payment_holds",
      group: "Partners",
      opsSubGroup: "Financeiro",
      newTag: "New9",
    },
    {
      to: "/ops/partners/admin?tab=billing",
      label: "Parceiros — billing",
      aria: "Planos, ciclos e line items",
      group: "Partners",
      opsSubGroup: "Financeiro",
      newTag: "New10",
    },
    {
      to: "/ops/partners/admin?tab=commission",
      label: "Parceiros — comissão",
      aria: "partner_commission_structure",
      group: "Partners",
      opsSubGroup: "Financeiro",
      newTag: "New11",
    },
    {
      to: "/ops/partners/admin?tab=sla",
      label: "Parceiros — SLA",
      aria: "partner_sla_agreements",
      group: "Partners",
      opsSubGroup: "Cadastro",
      newTag: "New12",
    },
    {
      to: "/ops/partners/admin?tab=status",
      label: "Parceiros — histórico status",
      aria: "partner_status_history",
      group: "Partners",
      opsSubGroup: "Cadastro",
      newTag: "New13",
    },
    {
      to: "/ops/partners/admin?tab=ecosystem",
      label: "Parceiros — redes mundiais",
      aria: "InPost, DHL, Magalu, Mercado Livre, Amazon, DPD, Correios, CTT, Worten, El Corte Inglés",
      group: "Partners",
      opsSubGroup: "Cadastro",
      newTag: "New14",
    },
    {
      to: "/ops/partners/admin?tab=global_ops",
      label: "Parceiros — Global OPS",
      aria: "Corredores, certificacoes, SLA por rota, prontidao por player",
      group: "Partners",
      opsSubGroup: "Global OPS",
      newTag: "New15",
    },
    {
      to: "/ops/partners/admin?tab=capability_webhooks",
      label: "Parceiros — webhooks capability (DLQ)",
      aria: "Espelho marketplace, dead-letter e replay em lote",
      group: "Partners",
      opsSubGroup: "Integração",
      newTag: "New16",
    },
    {
      to: "/ops/tenants/admin",
      label: "Tenants — white label",
      aria: "CRUD tenants, dominios e vinculos",
      group: "Partners",
      opsSubGroup: "Tenants",
    },
    { to: "/ops/partners/dashboard", label: "ops /partners/dashboard", aria: "Dashboard OPS de Partners", group: "Partners", opsSubGroup: "Financeiro" },
    { to: "/ops/partners/financials-service-areas", label: "ops /partners/financials-service-areas", aria: "Operacao P-3 para settlements, performance e service-areas", group: "Partners" },
    { to: "/ops/partners/settlement", label: "ops /partners/settlement", aria: "Batches e itens de settlement por parceiro com export CSV/JSON", group: "Partners" },
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
    "Cadastros OPS",
    "ML OPS",
    "Marketplace OPS",
    "Privacy & Compliance OPS",
    "Order / Pickup",
    "Lockers",
    "Inteligência",
    "Rentals OPS",
    "Runtime",
    "Logística",
    "Logística / Inventário",
    "Produtos & Catálogo",
    "Marketing",
    "Billing / Fiscal",
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
  const fiscalLinks = opsEnabled
    ? [
        { to: "/fiscal", label: "fiscal /global", aria: "Catálogo e matriz fiscal global" },
        { to: "/fiscal/countries", label: "fiscal /countries", aria: "Cockpit FG-1/FG-2 por país" },
        { to: "/fiscal/fg1-gate", label: "fiscal /fg1-gate", aria: "Gate técnico FG-1 (GO/NO_GO)" },
        { to: "/fiscal/readiness-execution", label: "fiscal /readiness-execution", aria: "Execução operacional de readiness FG-1" },
        { to: "/fiscal/management-daily", label: "fiscal /management-daily", aria: "Gestão diária contábil/fiscal" },
        {
          to: "/fiscal/sprint2-finance-gate",
          label: "fiscal /sprint2-finance-gate",
          aria: "Gate financeiro Sprint 2 (comité v2) e sprint ideal na sequência",
        },
        {
          to: "/fiscal/sprint3-partner-audit",
          label: "fiscal /sprint3-partner-audit",
          aria: "Sprint 3 P0-1 — auditoria E2E rollup por parceiro",
        },
        { to: "/fiscal/department-dashboards", label: "fiscal /department-dashboards", aria: "Dashboards departamentais fiscal e contábil" },
        { to: "/fiscal/partner-performance", label: "fiscal /partner-performance", aria: "Desempenho operacional de parceiros fiscais" },
        { to: "/fiscal/accounting-close", label: "fiscal /accounting-close", aria: "Fechamento contábil e fiscal diário" },
        { to: "/fiscal/slo-alerts", label: "fiscal /slo-alerts", aria: "Scorecards e alertas SLO fiscal/ops" },
        {
          to: "/fiscal/sprint4-regression-matrix",
          label: "fiscal /sprint4-regression-matrix",
          aria: "Matriz mínima de regressão Sprint 4 (por persona)",
        },
        {
          to: "/fiscal/incident-response",
          label: "fiscal /incident-response",
          aria: "Runbook e checklist de resposta a incidente fiscal/ops",
        },
        { to: "/fiscal/updates", label: "fiscal /updates", aria: "Histórico da trilha fiscal global" },
      ]
    : [];

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
          
          {opsEnabled && canAccessBackofficeMenus && opsLinks.length > 0 && (
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
                        {clusterOpsLinksBySubGroup(groupEntry.links).map((bucket, bidx) => (
                          <div key={`${groupEntry.group}-sg-${bidx}`}>
                            {bucket.subGroupLabel ? (
                              <div className="ops-subgroup-title" style={{ padding: "6px 12px 2px", fontSize: 11, color: "#94a3b8", fontWeight: 700 }}>
                                {bucket.subGroupLabel}
                              </div>
                            ) : null}
                            {bucket.links.map((link) => (
                              <Link
                                key={link.to}
                                className="nav-ops-item"
                                to={link.to}
                                onClick={() => setIsOpsMenuOpen(false)}
                              >
                                <span>{link.label}</span>
                                {link.newTag ? <span className="nav-new-badge">{link.newTag}</span> : null}
                              </Link>
                            ))}
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            </>
          )}

          {opsEnabled && canAccessBackofficeMenus && (
            <>
              <div className="nav-divider" aria-hidden="true">|</div>
              <InteligenciaMenu
                menuRef={intelMenuRef}
                buttonRef={intelButtonRef}
                isOpen={isIntelMenuOpen}
                setOpen={setIsIntelMenuOpen}
                atRiskCount={intelAtRiskBadge}
                pathname={location.pathname}
              />
            </>
          )}

          {opsEnabled && canAccessBackofficeMenus && fiscalLinks.length > 0 && (
            <>
              <div className="nav-divider" aria-hidden="true">|</div>
              <div
                className="nav-ops-dropdown"
                role="group"
                aria-label="Ferramentas fiscais"
                ref={fiscalMenuRef}
              >
                <button
                  ref={fiscalButtonRef}
                  type="button"
                  className="nav-link nav-link--fiscal nav-ops-toggle"
                  onClick={() => setIsFiscalMenuOpen((value) => !value)}
                  aria-haspopup="menu"
                  aria-expanded={isFiscalMenuOpen}
                >
                  FISCAL menu ({fiscalLinks.length}) {isFiscalMenuOpen ? "▲" : "▼"}
                </button>
                {isFiscalMenuOpen ? (
                  <div className="nav-fiscal-panel" role="menu" aria-label="Menu FISCAL">
                    {fiscalLinks.map((link) => (
                      <Link
                        key={link.to}
                        className="nav-fiscal-item"
                        to={link.to}
                        onClick={() => setIsFiscalMenuOpen(false)}
                      >
                        <span>{link.label}</span>
                        {link.newTag ? <span className="nav-new-badge">{link.newTag}</span> : null}
                      </Link>
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

      {(isOpsRoute || isFiscalRoute || isIntelligenceRoute) && (
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
            {isFiscalRoute ? (
              <span className="context-fiscal-badge">
                Contexto Fiscal
              </span>
            ) : null}
            {isIntelligenceRoute ? (
              <span style={{ padding: "2px 8px", borderRadius: 8, border: "1px solid rgba(167,139,250,0.5)", color: "#ddd6fe", fontWeight: 700 }}>
                ML / Inteligência
              </span>
            ) : null}
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
                          {link.newTag ? <span className="nav-new-badge">{link.newTag}</span> : null}
                        </Link>
                      ))}
                    </div>
                  ) : null}
                </div>
              )}

              {/* Links de operação */}
              {opsEnabled && canAccessBackofficeMenus && opsLinks.length > 0 && (
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
                          {clusterOpsLinksBySubGroup(groupEntry.links).map((bucket, bidx) => (
                            <div key={`${groupEntry.group}-m-sg-${bidx}`}>
                              {bucket.subGroupLabel ? (
                                <div className="ops-subgroup-title" style={{ padding: "6px 12px 2px", fontSize: 11, color: "#94a3b8", fontWeight: 700 }}>
                                  {bucket.subGroupLabel}
                                </div>
                              ) : null}
                              {bucket.links.map((link) => (
                                <Link
                                  key={link.to}
                                  className="mobile-nav-link mobile-nav-link--dev"
                                  to={link.to}
                                  onClick={() => setIsMobileMenuOpen(false)}
                                >
                                  <span>{link.label}</span>
                                  {link.newTag ? <span className="nav-new-badge">{link.newTag}</span> : null}
                                </Link>
                              ))}
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              )}

              {opsEnabled && canAccessBackofficeMenus && (
                <div className="mobile-menu-section">
                  <button
                    type="button"
                    className="mobile-ops-toggle"
                    onClick={() => setIsMobileIntelOpen((value) => !value)}
                    aria-expanded={isMobileIntelOpen}
                  >
                    Inteligência ML {intelAtRiskBadge > 0 ? `(${intelAtRiskBadge})` : ""} {isMobileIntelOpen ? "▲" : "▼"}
                  </button>
                  {isMobileIntelOpen ? (
                    <div className="mobile-ops-list">
                      <Link className="mobile-nav-link" to="/intelligence/dashboard" onClick={() => setIsMobileMenuOpen(false)}>
                        Dashboard ML
                      </Link>
                      <Link className="mobile-nav-link" to="/intelligence/models" onClick={() => setIsMobileMenuOpen(false)}>
                        Monitor de Modelos
                      </Link>
                      <Link className="mobile-nav-link" to="/intelligence/at-risk" onClick={() => setIsMobileMenuOpen(false)}>
                        Lockers em Risco
                      </Link>
                      <Link className="mobile-nav-link" to="/intelligence/history" onClick={() => setIsMobileMenuOpen(false)}>
                        Histórico
                      </Link>
                      <Link className="mobile-nav-link" to="/intelligence/dynamic-pricing" onClick={() => setIsMobileMenuOpen(false)}>
                        Preços dinâmicos
                      </Link>
                      <Link className="mobile-nav-link" to="/intelligence/occupancy-forecast" onClick={() => setIsMobileMenuOpen(false)}>
                        Previsão de ocupação
                      </Link>
                      <Link className="mobile-nav-link" to="/intelligence/pickup-fraud" onClick={() => setIsMobileMenuOpen(false)}>
                        Fraude pickups
                      </Link>
                      <Link className="mobile-nav-link" to="/intelligence/partner-churn" onClick={() => setIsMobileMenuOpen(false)}>
                        Churn parceiros
                      </Link>
                      <Link className="mobile-nav-link" to="/intelligence/ltv-scores" onClick={() => setIsMobileMenuOpen(false)}>
                        LTV clientes
                      </Link>
                      <Link className="mobile-nav-link" to="/intelligence/route-optimize" onClick={() => setIsMobileMenuOpen(false)}>
                        Roteirização ML
                      </Link>
                      <Link className="mobile-nav-link" to="/intelligence/feedback-nlp" onClick={() => setIsMobileMenuOpen(false)}>
                        Feedback &amp; NLP
                      </Link>
                    </div>
                  ) : null}
                </div>
              )}

              {opsEnabled && canAccessBackofficeMenus && fiscalLinks.length > 0 && (
                <div className="mobile-menu-section">
                  <button
                    type="button"
                    className="mobile-fiscal-toggle"
                    onClick={() => setIsMobileFiscalOpen((value) => !value)}
                    aria-expanded={isMobileFiscalOpen}
                  >
                    Fiscal ({fiscalLinks.length}) {isMobileFiscalOpen ? "▲" : "▼"}
                  </button>
                  {isMobileFiscalOpen ? (
                    <div className="mobile-ops-list">
                      {fiscalLinks.map((link) => (
                        <Link
                          key={link.to}
                          className="mobile-nav-link mobile-nav-link--fiscal"
                          to={link.to}
                          onClick={() => setIsMobileMenuOpen(false)}
                        >
                          <span>{link.label}</span>
                          {link.newTag ? <span className="nav-new-badge">{link.newTag}</span> : null}
                        </Link>
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
  const allowed = hasAnyRole(hasRole, ["admin.operacao", "suporte", "auditoria"]);
  if (!allowed) {
    return <Navigate to="/acesso-negado" replace />;
  }
  return children;
}

function IntelligenceRoute({ children }) {
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
  const allowed = hasAnyRole(hasRole, ["admin.operacao", "admin.financeiro"]);
  if (!allowed) {
    return <Navigate to="/acesso-negado" replace />;
  }
  return children;
}

function RecoverFiscalRoute() {
  const location = useLocation();
  const normalizedPath = String(location.pathname || "").toLowerCase();
  if (normalizedPath.includes("fiscal/countries")) {
    return <Navigate to="/fiscal/countries" replace />;
  }
  if (normalizedPath.includes("fiscal/sprint3-partner-audit")) {
    return <Navigate to="/fiscal/sprint3-partner-audit" replace />;
  }
  if (normalizedPath.includes("fiscal/sprint2-finance-gate")) {
    return <Navigate to="/fiscal/sprint2-finance-gate" replace />;
  }
  if (normalizedPath.includes("fiscal/sprint4-regression-matrix")) {
    return <Navigate to="/fiscal/sprint4-regression-matrix" replace />;
  }
  if (normalizedPath.includes("fiscal/updates")) {
    return <Navigate to="/fiscal/updates" replace />;
  }
  if (normalizedPath.includes("fiscal/fg1-gate")) {
    return <Navigate to="/fiscal/fg1-gate" replace />;
  }
  if (normalizedPath.includes("fiscal/readiness-execution")) {
    return <Navigate to="/fiscal/readiness-execution" replace />;
  }
  if (normalizedPath.includes("fiscal/management-daily")) {
    return <Navigate to="/fiscal/management-daily" replace />;
  }
  if (normalizedPath.includes("fiscal/department-dashboards")) {
    return <Navigate to="/fiscal/department-dashboards" replace />;
  }
  if (normalizedPath.includes("fiscal/partner-performance")) {
    return <Navigate to="/fiscal/partner-performance" replace />;
  }
  if (normalizedPath.includes("fiscal/accounting-close")) {
    return <Navigate to="/fiscal/accounting-close" replace />;
  }
  if (normalizedPath.includes("fiscal/slo-alerts")) {
    return <Navigate to="/fiscal/slo-alerts" replace />;
  }
  if (normalizedPath.includes("fiscal/incident-response")) {
    return <Navigate to="/fiscal/incident-response" replace />;
  }
  if (normalizedPath.includes("fiscal/global") || normalizedPath.includes("/fiscal")) {
    return <Navigate to="/fiscal" replace />;
  }
  return <PublicNotFoundPage />;
}

/** Agrupa links OPS consecutivos com o mesmo `opsSubGroup` (ex.: Products → categories). */
function clusterOpsLinksBySubGroup(links) {
  const out = [];
  for (const link of links) {
    const sub = link.opsSubGroup ? String(link.opsSubGroup) : null;
    const prev = out[out.length - 1];
    if (prev && prev.subGroupLabel === sub) {
      prev.links.push(link);
    } else {
      out.push({ subGroupLabel: sub, links: [link] });
    }
  }
  return out;
}

function AppContent() {
  const location = useLocation();
  const path = String(location.pathname || "").toLowerCase();

  const logBoundaryError = (domain) => (error, errorInfo) => {
    reportUiErrorTelemetry({
      domain,
      path: location.pathname,
      error,
      errorInfo,
    });
  };

  const withBoundary = (domain, element) => (
    <DomainErrorBoundary key={`${domain}:${location.pathname}`} domain={domain} onError={logBoundaryError(domain)}>
      {element}
    </DomainErrorBoundary>
  );

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
            <Route path="/checkout" element={withBoundary("checkout", <PublicCheckoutPage />)} />
            <Route path="/comprovante" element={<PublicFiscalSearchPage />} />
            <Route path="/suporte" element={<PublicSupportPage />} /> {/* NOVA ROTA */}
            <Route path="/privacidade" element={<PublicPrivacyPolicyPage />} />
            <Route path="/legal/privacy" element={<PublicLegalPrivacyIndexPage />} />
            <Route path="/legal/privacy/players" element={<PublicPlayerLegalPrivacyIndexPage />} />
            <Route path="/legal/privacy/player/:playerCode/:version" element={<PublicPlayerLegalPrivacyDocumentPage />} />
            <Route path="/legal/privacy/:region/:version" element={<PublicLegalPrivacyDocumentPage />} />
            <Route path="/termos" element={<PublicTermsOfUsePage />} />
            <Route path="/sp" element={<PublicRegionHubPage region="SP" />} />
            <Route path="/pt" element={<PublicRegionHubPage region="PT" />} />
            <Route
              path="/meus-pedidos"
              element={
                <PrivateRoute>
                  {withBoundary("orders", <PublicMyOrdersPage />)}
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
                  {withBoundary("orders", <PublicOrderDetailPage />)}
                </PrivateRoute>
              }
            />
            <Route path="/verificar-email" element={<PublicEmailVerificationPage />} />
            <Route path="/acesso-negado" element={<PublicAccessDeniedPage />} />
            <Route path="/intelligence" element={<Navigate to="/intelligence/dashboard" replace />} />
            <Route
              path="/intelligence/dashboard"
              element={
                <IntelligenceRoute>
                  {withBoundary("intelligence", <InteligenciaDashboardPage />)}
                </IntelligenceRoute>
              }
            />
            <Route
              path="/intelligence/models"
              element={
                <IntelligenceRoute>
                  {withBoundary("intelligence", <ModelMonitorPage />)}
                </IntelligenceRoute>
              }
            />
            <Route
              path="/intelligence/at-risk"
              element={
                <IntelligenceRoute>
                  {withBoundary("intelligence", <AtRiskLockersPage />)}
                </IntelligenceRoute>
              }
            />
            <Route
              path="/intelligence/history"
              element={
                <IntelligenceRoute>
                  {withBoundary("intelligence", <PredictionHistoryPage />)}
                </IntelligenceRoute>
              }
            />
            <Route
              path="/intelligence/partner-churn"
              element={
                <IntelligenceRoute>
                  {withBoundary("intelligence", <PartnerChurnPage />)}
                </IntelligenceRoute>
              }
            />
            <Route
              path="/intelligence/ltv-scores"
              element={
                <IntelligenceRoute>
                  {withBoundary("intelligence", <CustomerLTVScoresPage />)}
                </IntelligenceRoute>
              }
            />
            <Route
              path="/intelligence/dynamic-pricing"
              element={
                <IntelligenceRoute>
                  {withBoundary("intelligence", <DynamicPricingPage />)}
                </IntelligenceRoute>
              }
            />
            <Route
              path="/intelligence/occupancy-forecast"
              element={
                <IntelligenceRoute>
                  {withBoundary("intelligence", <OccupancyForecastIntelPage />)}
                </IntelligenceRoute>
              }
            />
            <Route
              path="/intelligence/pickup-fraud"
              element={
                <IntelligenceRoute>
                  {withBoundary("intelligence", <PickupFraudDashboardPage />)}
                </IntelligenceRoute>
              }
            />
            <Route
              path="/intelligence/route-optimize"
              element={
                <IntelligenceRoute>
                  {withBoundary("intelligence", <RouteOptimizePage />)}
                </IntelligenceRoute>
              }
            />
            <Route
              path="/intelligence/feedback-nlp"
              element={
                <IntelligenceRoute>
                  {withBoundary("intelligence", <FeedbackNlpDashboardPage />)}
                </IntelligenceRoute>
              }
            />
            <Route
              path="/fiscal"
              element={
                <OpsRoute>
                  <FiscalPageLayout>
                    <FiscalGlobalPage />
                  </FiscalPageLayout>
                </OpsRoute>
              }
            />
            <Route
              path="/fiscal/countries"
              element={
                <OpsRoute>
                  <FiscalPageLayout>
                    <FiscalCountriesPage />
                  </FiscalPageLayout>
                </OpsRoute>
              }
            />
            <Route
              path="/fiscal/fg1-gate"
              element={
                <OpsRoute>
                  <FiscalPageLayout>
                    <FiscalFg1GatePage />
                  </FiscalPageLayout>
                </OpsRoute>
              }
            />
            <Route
              path="/fiscal/updates"
              element={
                <OpsRoute>
                  <FiscalPageLayout>
                    <FiscalUpdatesPage />
                  </FiscalPageLayout>
                </OpsRoute>
              }
            />
            <Route
              path="/fiscal/readiness-execution"
              element={
                <OpsRoute>
                  <FiscalPageLayout>
                    <FiscalReadinessExecutionPage />
                  </FiscalPageLayout>
                </OpsRoute>
              }
            />
            <Route
              path="/fiscal/management-daily"
              element={
                <OpsRoute>
                  <FiscalPageLayout>
                    <FiscalManagementDailyPage />
                  </FiscalPageLayout>
                </OpsRoute>
              }
            />
            <Route
              path="/fiscal/sprint2-finance-gate"
              element={
                <OpsRoute>
                  <FiscalPageLayout>
                    <FiscalSprint2FinanceGatePage />
                  </FiscalPageLayout>
                </OpsRoute>
              }
            />
            <Route
              path="/fiscal/sprint3-partner-audit"
              element={
                <OpsRoute>
                  <FiscalPageLayout>
                    <FiscalSprint3PartnerAuditPage />
                  </FiscalPageLayout>
                </OpsRoute>
              }
            />
            <Route
              path="/fiscal/department-dashboards"
              element={
                <OpsRoute>
                  <FiscalPageLayout>
                    <FiscalDepartmentDashboardsPage />
                  </FiscalPageLayout>
                </OpsRoute>
              }
            />
            <Route
              path="/fiscal/partner-performance"
              element={
                <OpsRoute>
                  <FiscalPageLayout>
                    <FiscalPartnerPerformancePage />
                  </FiscalPageLayout>
                </OpsRoute>
              }
            />
            <Route
              path="/fiscal/accounting-close"
              element={
                <OpsRoute>
                  <FiscalPageLayout>
                    <FiscalAccountingClosePage />
                  </FiscalPageLayout>
                </OpsRoute>
              }
            />
            <Route
              path="/fiscal/slo-alerts"
              element={
                <OpsRoute>
                  <FiscalPageLayout>
                    <FiscalSloAlertsPage />
                  </FiscalPageLayout>
                </OpsRoute>
              }
            />
            <Route
              path="/fiscal/sprint4-regression-matrix"
              element={
                <OpsRoute>
                  <FiscalPageLayout>
                    <FiscalSprint4RegressionMatrixPage />
                  </FiscalPageLayout>
                </OpsRoute>
              }
            />
            <Route
              path="/fiscal/incident-response"
              element={
                <OpsRoute>
                  <FiscalPageLayout>
                    <FiscalIncidentResponsePage />
                  </FiscalPageLayout>
                </OpsRoute>
              }
            />
            <Route
              path="/ops/sp"
              element={
                <OpsRoute>
                  {withBoundary("ops", <LockerDashboard region="SP" />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/pt"
              element={
                <OpsRoute>
                  {withBoundary("ops", <LockerDashboard region="PT" />)}
                </OpsRoute>
              }
            />


            <Route
              path="/ops/00"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsDiscontinuedEllanLabPage />)}
                </OpsRoute>
              }
            />


            <Route
              path="/ops/sp/kiosk"
              element={
                <OpsRoute>
                  {withBoundary("ops", <RegionPage region="SP" mode="kiosk" />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/pt/kiosk"
              element={
                <OpsRoute>
                  {withBoundary("ops", <RegionPage region="PT" mode="kiosk" />)}
                </OpsRoute>
              }
            />




            <Route
              path="/ops/00/kiosk"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsDiscontinuedEllanLabPage />)}
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
                  {withBoundary("ops", <OpsReconciliationPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/audit"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsAuditPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/notifications/logs"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsNotificationLogsPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/health"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsHealthPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/runtime/health"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsRuntimeHealthPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/runtime/events"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsRuntimeEventLogPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/runtime/slots"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsRuntimeSlotsMonitorPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/runtime/sync"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsRuntimeSyncPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/quick-enablement"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsQuickEnablementPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/kiosk-touch-models"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsKioskTouchModelsPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/dev/errors"
              element={
                <OpsRoute>
                  <OpsDevErrorsPage />
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
              path="/ops/returns/tracking"
              element={
                <OpsRoute>
                  <OpsReturnTrackingPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/logistics/inventory"
              element={
                <OpsRoute>
                  <OpsLogisticsInventoryPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/logistics/route-optimize"
              element={
                <OpsRoute>
                  {withBoundary("ops", <RouteOptimizePage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/lockers/product-configs"
              element={
                <OpsRoute>
                  <OpsLockerProductConfigPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/lockers/create"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsLockerCreatePage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/partners/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsPartnersAdminPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/access/user-roles"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsUserRolesPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/tenants/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsTenantsAdminPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/payment-gateway/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsPaymentGatewayAdminPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/order-pickup/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsOrderPickupAdminPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/marketplace/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsMarketplaceAdminPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/finance/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsFinanceAdminPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/privacy-compliance/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsPrivacyComplianceAdminPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/ml/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsMlAdminPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/lockers/slots"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsLockerSlotsPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/lockers/occupancy-forecast"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsLockerOccupancyForecastPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/lockers/operators"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsLockerOperatorsPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/rentals/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsRentalAdminPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/rentals/contracts/:id"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsRentalContractsPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/rentals/contracts"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsRentalContractsPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/rentals/plans"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsRentalPlansPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/products/admin"
              element={
                <OpsRoute>
                  <OpsProductsAdminRedirect />
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
              path="/ops/products/categories"
              element={
                <OpsRoute>
                  <OpsProductCategoriesPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/products/ecosystem"
              element={
                <OpsRoute>
                  <OpsProductsEcosystemPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/products/professional"
              element={
                <OpsRoute>
                  <OpsProductsProfessionalPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/products/bundles"
              element={
                <OpsRoute>
                  <OpsProductBundlesPage />
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
              path="/ops/products/pricing-rules"
              element={
                <OpsRoute>
                  <OpsPricingRulesPage />
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
              path="/ops/marketing/promotions"
              element={
                <OpsRoute>
                  <OpsPromotionsAdminPage />
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
              path="/ops/partners/settlement"
              element={
                <OpsRoute>
                  <PartnerSettlementPage />
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
              path="/ops/billing/invoices"
              element={
                <OpsRoute>{withBoundary("ops", <BillingInvoiceSearchPage />)}</OpsRoute>
              }
            />
            <Route
              path="/ops/billing/invoice-queue"
              element={
                <OpsRoute>{withBoundary("ops", <BillingInvoiceQueuePage />)}</OpsRoute>
              }
            />
            <Route
              path="/ops/billing/reconciliation-gaps"
              element={
                <OpsRoute>{withBoundary("ops", <BillingReconciliationGapsPage />)}</OpsRoute>
              }
            />
            <Route
              path="/ops/billing/kpis"
              element={
                <OpsRoute>{withBoundary("ops", <BillingKpiDailyPage />)}</OpsRoute>
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
            <Route path="/ops/analytics/pickup" element={<Navigate to="/ops/order/pickup-health" replace />} />
            <Route
              path="/ops/order/executive-summary"
              element={
                <OpsRoute>
                  <OrderPickupExecutiveSummaryPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/order/pickup-health"
              element={
                <OpsRoute>
                  <OrderPickupHealthPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/intelligence"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsIntelligencePage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/feedback-nlp"
              element={
                <OpsRoute>
                  {withBoundary("ops", <FeedbackNlpDashboardPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/order/domain-events"
              element={
                <OpsRoute>
                  <OrderDomainEventsPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/order/deadlines"
              element={
                <OpsRoute>
                  <OrderDeadlinesPage />
                </OpsRoute>
              }
            />
            <Route
              path="/ops/payments/reconciliation"
              element={
                <OpsRoute>
                  {withBoundary("ops", <PaymentReconciliationPage />)}
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
            <Route path="*" element={<RecoverFiscalRoute />} />
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
            to="/legal/privacy" 
            style={{ 
              textDecoration: 'none',
              color: 'inherit',
              transition: 'color var(--transition-base)'
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#667eea'}
            onMouseLeave={(e) => e.currentTarget.style.color = 'inherit'}
          >
            Documentos legais
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

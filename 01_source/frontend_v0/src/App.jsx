
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
const OpsLockerProductConfigPage = lazy(() => import("./pages/OpsLockerProductConfigPage"));
const OpsLockerSlotsPage = lazy(() => import("./pages/OpsLockerSlotsPage"));
const OpsLockerOccupancyForecastPage = lazy(() => import("./pages/OpsLockerOccupancyForecastPage"));
const OpsLockerOperatorsPage = lazy(() => import("./pages/OpsLockerOperatorsPage"));
const OpsRentalContractsPage = lazy(() => import("./pages/OpsRentalContractsPage"));
const OpsRentalPlansPage = lazy(() => import("./pages/OpsRentalPlansPage"));
const OpsProductBundlesPage = lazy(() => import("./pages/OpsProductBundlesPage"));
const OpsPromotionsPage = lazy(() => import("./pages/OpsPromotionsPage"));
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
      isNew: true,
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
      isNew: true,
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
      isNew: true,
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
      isNew: true,
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
      to: "/ops/rentals/contracts",
      label: "ops /rentals/contracts",
      aria: "Listagem interna de contratos de aluguel (rental_contracts)",
      group: "Rentals",
      opsSubGroup: "Rentals",
    },
    {
      to: "/ops/rentals/plans",
      label: "ops /rentals/plans",
      aria: "Planos de aluguel ativos (rental_plans, admin_operacao)",
      group: "Rentals",
      opsSubGroup: "Rentals",
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
      to: "/ops/products/catalog",
      label: "ops /products/catalog",
      aria: "Dashboard OPS de Catalogo de produtos",
      group: "Produtos & Fiscal",
      opsSubGroup: "Products",
    },
    {
      to: "/ops/products/assets",
      label: "ops /products/assets",
      aria: "Operacao OPS para media e barcodes de produtos",
      group: "Produtos & Fiscal",
      opsSubGroup: "Products",
    },
    {
      to: "/ops/products/categories",
      label: "ops /products/categories",
      aria: "CRUD OPS de product_categories (arvore hierarquica)",
      group: "Produtos & Fiscal",
      opsSubGroup: "Products",
    },
    {
      to: "/ops/products/bundles",
      label: "ops /products/bundles",
      aria: "Listagem OPS de product_bundles e itens (ativar/desativar)",
      group: "Produtos & Fiscal",
      opsSubGroup: "Products",
    },
    {
      to: "/ops/products/pricing-fiscal",
      label: "ops /products/pricing-fiscal",
      aria: "Operacao OPS para pricing e fiscal do Pr-3",
      group: "Produtos & Fiscal",
      opsSubGroup: "Products",
    },
    {
      to: "/ops/products/pricing-rules",
      label: "ops /products/pricing-rules",
      aria: "Regras comerciais pricing_rules (regiao, categoria, vigencia)",
      group: "Produtos & Fiscal",
      opsSubGroup: "Products",
    },
    {
      to: "/ops/products/inventory-health",
      label: "ops /products/inventory-health",
      aria: "Dashboard OPS de Inventory Health",
      group: "Produtos & Fiscal",
      opsSubGroup: "Products",
    },
    { to: "/ops/marketing/promotions", label: "ops /marketing/promotions", aria: "Listagem e CRUD basico de promocoes (PR3)", group: "Marketing" },
    { to: "/ops/billing/invoices", label: "ops /billing/invoices", aria: "Busca de invoice (internal)", group: "Billing / Fiscal" },
    { to: "/ops/billing/invoice-queue", label: "ops /billing/invoice-queue", aria: "Fila operacional (dead letters + gaps)", group: "Billing / Fiscal" },
    { to: "/ops/billing/reconciliation-gaps", label: "ops /billing/reconciliation-gaps", aria: "Gaps de reconciliação fiscal", group: "Billing / Fiscal" },
    { to: "/ops/billing/kpis", label: "ops /billing/kpis", aria: "KPI financeiro diário (FA-5)", group: "Billing / Fiscal" },
    { to: "/ops/fiscal/providers", label: "ops /fiscal/providers", aria: "Status de providers fiscais BR/PT", group: "Produtos & Fiscal" },
    { to: "/ops/integration/outbox-replay", label: "ops /integration/outbox-replay", aria: "Operacao de replay em lote do outbox de integracao", group: "Integrações" },
    { to: "/ops/integration/orders-fiscal", label: "ops /integration/orders-fiscal", aria: "Operacao I-1 por order_id (fulfillment, events, fiscal)", group: "Integrações" },
    { to: "/ops/integration/orders-partner-lookup", label: "ops /integration/orders-partner-lookup", aria: "Operacao L-3 para lookup dedicado por partner/ref", group: "Integrações" },
    { to: "/ops/partners/dashboard", label: "ops /partners/dashboard", aria: "Dashboard OPS de Partners", group: "Partners" },
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
    "Order / Pickup",
    "Lockers",
    "Rentals",
    "Runtime",
    "Logística",
    "Logística / Inventário",
    "Produtos & Fiscal",
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
          isNew: true,
        },
        {
          to: "/fiscal/sprint3-partner-audit",
          label: "fiscal /sprint3-partner-audit",
          aria: "Sprint 3 P0-1 — auditoria E2E rollup por parceiro",
          isNew: true,
        },
        { to: "/fiscal/department-dashboards", label: "fiscal /department-dashboards", aria: "Dashboards departamentais fiscal e contábil" },
        { to: "/fiscal/partner-performance", label: "fiscal /partner-performance", aria: "Desempenho operacional de parceiros fiscais" },
        { to: "/fiscal/accounting-close", label: "fiscal /accounting-close", aria: "Fechamento contábil e fiscal diário" },
        { to: "/fiscal/slo-alerts", label: "fiscal /slo-alerts", aria: "Scorecards e alertas SLO fiscal/ops" },
        {
          to: "/fiscal/sprint4-regression-matrix",
          label: "fiscal /sprint4-regression-matrix",
          aria: "Matriz mínima de regressão Sprint 4 (por persona)",
          isNew: true,
        },
        {
          to: "/fiscal/incident-response",
          label: "fiscal /incident-response",
          aria: "Runbook e checklist de resposta a incidente fiscal/ops",
          isNew: true,
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
                                {link.isNew ? <span className="nav-new-badge">NEW</span> : null}
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
                        {link.isNew ? <span className="nav-new-badge">NEW</span> : null}
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
                          {link.isNew ? <span className="nav-new-badge">NEW</span> : null}
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
                                  {link.isNew ? <span className="nav-new-badge">NEW</span> : null}
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
                          {link.isNew ? <span className="nav-new-badge">NEW</span> : null}
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
                  <OpsPromotionsPage />
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

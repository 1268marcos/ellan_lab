
// 01_source/frontend/src/App.jsx
import React, { Suspense, lazy, useState, useEffect, useRef } from "react";
import { Routes, Route, Navigate, Link, useLocation, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import InteligenciaMenu from "./components/intelligence/InteligenciaMenu";
import OpsMenuPanel from "./components/ops/OpsMenuPanel";
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
const PublicCookiePolicyPage = lazy(() => import("./pages/public/PublicCookiePolicyPage"));
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
const OpsUsersSecurityAdminPage = lazy(() => import("./pages/OpsUsersSecurityAdminPage"));
const OpsTenantsAdminPage = lazy(() => import("./pages/OpsTenantsAdminPage"));
const SecurityShell = lazy(() => import("./pages/security/SecurityShell"));
const SecurityUsersList = lazy(() => import("./pages/security/SecurityPages").then((m) => ({ default: m.UsersList })));
const SecurityUserForm = lazy(() => import("./pages/security/SecurityPages").then((m) => ({ default: m.UserForm })));
const SecurityUserDetail = lazy(() => import("./pages/security/SecurityPages").then((m) => ({ default: m.UserDetail })));
const SecurityRolesList = lazy(() => import("./pages/security/SecurityPages").then((m) => ({ default: m.RolesList })));
const SecurityRoleForm = lazy(() => import("./pages/security/SecurityPages").then((m) => ({ default: m.RoleForm })));
const SecurityRoleDetail = lazy(() => import("./pages/security/SecurityPages").then((m) => ({ default: m.RoleDetail })));
const SecurityPermissionsMatrix = lazy(() =>
  import("./pages/security/SecurityPages").then((m) => ({ default: m.PermissionsMatrix })),
);
const SecurityApiKeysManager = lazy(() =>
  import("./pages/security/SecurityPages").then((m) => ({ default: m.ApiKeysManager })),
);
const SecurityWebhookConfig = lazy(() => import("./pages/security/SecurityPages").then((m) => ({ default: m.WebhookConfig })));
const IntegrationsShell = lazy(() =>
  import("./pages/integrations/IntegrationsPages").then((m) => ({ default: m.IntegrationsShell })),
);
const IntegrationsPartnersList = lazy(() =>
  import("./pages/integrations/IntegrationsPages").then((m) => ({ default: m.PartnersList })),
);
const IntegrationsPartnerDetail = lazy(() =>
  import("./pages/integrations/IntegrationsPages").then((m) => ({ default: m.PartnerDetail })),
);
const IntegrationsMarketplaces = lazy(() =>
  import("./pages/integrations/IntegrationsPages").then((m) => ({ default: m.MarketplaceConnections })),
);
const IntegrationsCarriers = lazy(() =>
  import("./pages/integrations/IntegrationsPages").then((m) => ({ default: m.CarrierRatesManager })),
);
const IntegrationsWebhooks = lazy(() =>
  import("./pages/integrations/IntegrationsPages").then((m) => ({ default: m.WebhooksHub })),
);
const OpsPaymentGatewayAdminPage = lazy(() => import("./pages/OpsPaymentGatewayAdminPage"));
const OpsHardwareAdminPage = lazy(() => import("./pages/OpsHardwareAdminPage"));
const OpsPaymentsAdminPage = lazy(() => import("./pages/OpsPaymentsAdminPage"));
const OpsMoneyCambioAdminPage = lazy(() => import("./pages/OpsMoneyCambioAdminPage"));
const OpsFiscalAdminPage = lazy(() => import("./pages/OpsFiscalAdminPage"));
const OpsOrderPickupAdminPage = lazy(() => import("./pages/OpsOrderPickupAdminPage"));
const OpsWorkersAdminPage = lazy(() => import("./pages/OpsWorkersAdminPage"));
const OpsLockersMapPage = lazy(() => import("./pages/OpsLockersMapPage"));
const OpsLockerDetailPage = lazy(() => import("./pages/OpsLockerDetailPage"));
const OpsMaintenanceTicketsPage = lazy(() => import("./pages/OpsMaintenanceTicketsPage"));
const OpsNocAlertsPage = lazy(() => import("./pages/OpsNocAlertsPage"));
const OpsSlaReportsPage = lazy(() => import("./pages/OpsSlaReportsPage"));
const OpsMarketplaceAdminPage = lazy(() => import("./pages/OpsMarketplaceAdminPage"));
const OpsFinanceAdminPage = lazy(() => import("./pages/OpsFinanceAdminPage"));
const OpsFinancialAnalyticsPage = lazy(() => import("./pages/OpsFinancialAnalyticsPage"));
const FinancialShell = lazy(() => import("./pages/financial/FinancialShell"));
const FinancialExecutiveDashboard = lazy(() => import("./pages/financial/ExecutiveDashboard"));
const FinancialLockerProfitability = lazy(() => import("./pages/financial/LockerProfitability"));
const FinancialExpansionSimulator = lazy(() => import("./pages/financial/ExpansionSimulator"));
const FinancialPartnerRevenue = lazy(() => import("./pages/financial/PartnerRevenue"));
const OpsPrivacyComplianceAdminPage = lazy(() => import("./pages/OpsPrivacyComplianceAdminPage"));
const OpsMlAdminPage = lazy(() => import("./pages/OpsMlAdminPage"));
const OpsRentalContractsPage = lazy(() => import("./pages/OpsRentalContractsPage"));
const OpsRentalPlansPage = lazy(() => import("./pages/OpsRentalPlansPage"));
const OpsRentalAdminPage = lazy(() => import("./pages/OpsRentalAdminPage"));
const OpsSubscriptionsAdminPage = lazy(() => import("./pages/OpsSubscriptionsAdminPage"));
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
      to: "/security/users",
      label: "Security — Users & Roles",
      aria: "CRUD usuarios e papeis admin ops finance support partner",
      group: "Security",
      opsSubGroup: "Users & Roles",
      newTag: "CRUD",
    },
    {
      to: "/security/permissions",
      label: "Security — Permissions",
      aria: "Matriz grupos security_permissions",
      group: "Security",
      opsSubGroup: "Permissions",
    },
    {
      to: "/security/api-keys",
      label: "Security — API Keys",
      aria: "Rotacao security_api_keys",
      group: "Security",
      opsSubGroup: "API Keys",
    },
    {
      to: "/security/webhooks",
      label: "Security — Webhooks",
      aria: "Configuracao security_webhook_endpoints",
      group: "Security",
      opsSubGroup: "Webhooks",
    },
    {
      to: "/integrations/partners",
      label: "Integrations — Partners",
      aria: "partner_ecosystem_players capabilities health",
      group: "Integrations",
      opsSubGroup: "Partners",
      newTag: "Hub",
    },
    {
      to: "/integrations/marketplaces",
      label: "Integrations — Marketplaces",
      aria: "marketplace_channel_partners connections",
      group: "Integrations",
      opsSubGroup: "Marketplaces",
    },
    {
      to: "/integrations/carriers",
      label: "Integrations — Carriers",
      aria: "logistics_carrier_rates DHL DPD InPost",
      group: "Integrations",
      opsSubGroup: "Carriers",
    },
    {
      to: "/integrations/webhooks",
      label: "Integrations — Webhooks",
      aria: "HMAC SHA256 webhook test",
      group: "Integrations",
      opsSubGroup: "Webhooks",
    },
    {
      to: "/ops/access/security-admin?tab=overview",
      label: "Users & Security — hub",
      aria: "Usuarios roles permissoes webhooks API keys auditoria",
      group: "Users & Security OPS",
      opsSubGroup: "Hub",
      newTag: "Hub",
    },
    {
      to: "/ops/access/security-admin?tab=domains",
      label: "Dominios OPS · health",
      aria: "PARTNER MARKETPLACE PAYMENT HARDWARE health probe",
      group: "Users & Security OPS",
      opsSubGroup: "Hub",
    },
    {
      to: "/ops/access/security-admin?tab=ecosystem",
      label: "Mapa ecossistema mundial",
      aria: "InPost DPD Magalu Mercado Livre entidades cross-domain",
      group: "Users & Security OPS",
      opsSubGroup: "Ecossistema mundial",
      newTag: "Pro",
    },
    {
      to: "/ops/access/security-admin?tab=locker-players",
      label: "Players locker mundial",
      aria: "InPost DHL Magalu Mercado Livre Amazon DPD Correios CTT Worten El Corte Ingles",
      group: "Users & Security OPS",
      opsSubGroup: "Ecossistema mundial",
      newTag: "Pro",
    },
    {
      to: "/ops/access/security-admin?tab=taxonomy",
      label: "Taxonomia mundial",
      aria: "Segmentos locker carrier marketplace food delivery PUDO agregador",
      group: "Users & Security OPS",
      opsSubGroup: "Ecossistema mundial",
    },
    {
      to: "/ops/access/security-admin?tab=relations",
      label: "Relacoes player",
      aria: "MercadoLivre InPost iFood agregadores carriers",
      group: "Users & Security OPS",
      opsSubGroup: "Ecossistema mundial",
      newTag: "Pro",
    },
    {
      to: "/ops/access/security-admin?tab=intelligence",
      label: "Inteligencia OPS",
      aria: "Postura risco alertas recomendacoes",
      group: "Users & Security OPS",
      opsSubGroup: "Hub",
      newTag: "Pro",
    },
    {
      to: "/ops/access/security-admin?tab=access-review",
      label: "Revisao de acesso",
      aria: "Campanha certificacao SOC2",
      group: "Users & Security OPS",
      opsSubGroup: "Governanca",
    },
    {
      to: "/ops/access/security-admin?tab=break-glass",
      label: "Break-glass",
      aria: "Acesso emergencia auditado",
      group: "Users & Security OPS",
      opsSubGroup: "Governanca",
      newTag: "P1",
    },
    {
      to: "/ops/access/security-admin?tab=access-requests",
      label: "Pedidos de acesso",
      aria: "Workflow aprovar grant cross-domain",
      group: "Users & Security OPS",
      opsSubGroup: "Cross-domain",
    },
    {
      to: "/ops/access/security-admin?tab=jit-access",
      label: "Acesso JIT",
      aria: "Grant temporario auto-expira",
      group: "Users & Security OPS",
      opsSubGroup: "Cross-domain",
    },
    {
      to: "/ops/access/security-admin?tab=delegations",
      label: "Delegacao act-as",
      aria: "Operar em nome de partner marketplace",
      group: "Users & Security OPS",
      opsSubGroup: "Cross-domain",
    },
    {
      to: "/ops/access/security-admin?tab=entitlements",
      label: "Entitlements remotos",
      aria: "Sync partner marketplace hardware",
      group: "Users & Security OPS",
      opsSubGroup: "Cross-domain",
    },
    {
      to: "/ops/access/security-admin?tab=alerts",
      label: "Alertas",
      aria: "API key stale break-glass risk",
      group: "Users & Security OPS",
      opsSubGroup: "Governanca",
    },
    {
      to: "/ops/access/security-admin?tab=compliance",
      label: "Compliance",
      aria: "LGPD GDPR SOC2 PCI mappings",
      group: "Users & Security OPS",
      opsSubGroup: "Governanca",
    },
    {
      to: "/ops/access/security-admin?tab=templates",
      label: "Templates onboarding",
      aria: "Carrier marketplace food delivery locker admin",
      group: "Users & Security OPS",
      opsSubGroup: "Governanca",
    },
    {
      to: "/ops/access/security-admin?tab=matrix",
      label: "Matriz acesso",
      aria: "Usuario dominio grants heatmap",
      group: "Users & Security OPS",
      opsSubGroup: "Governanca",
    },
    {
      to: "/ops/access/security-admin?tab=user-360",
      label: "Usuario 360",
      aria: "Visao unificada roles grants sessoes dominios",
      group: "Users & Security OPS",
      opsSubGroup: "Identidade",
      newTag: "Pro",
    },
    {
      to: "/ops/access/security-admin?tab=role-catalog",
      label: "Catalogo de roles",
      aria: "admin_operacao suporte carrier_ops partner_api",
      group: "Users & Security OPS",
      opsSubGroup: "Identidade",
    },
    {
      to: "/ops/access/security-admin?tab=grants",
      label: "Grants cross-domain",
      aria: "security_cross_domain_grants permissoes por entidade",
      group: "Users & Security OPS",
      opsSubGroup: "Integracao",
      newTag: "Pro",
    },
    {
      to: "/ops/access/security-admin?tab=deliveries",
      label: "Entregas webhook",
      aria: "security_webhook_deliveries status tentativas",
      group: "Users & Security OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/ops/access/security-admin?tab=sessions",
      label: "Sessoes ativas",
      aria: "security_user_sessions SSO API key",
      group: "Users & Security OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/ops/access/security-admin?tab=identity",
      label: "Identity / SSO",
      aria: "Okta Azure AD Google Workspace",
      group: "Users & Security OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/ops/access/security-admin?tab=policy",
      label: "Policy snapshots",
      aria: "RBAC versioning compliance",
      group: "Users & Security OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/ops/access/security-admin?tab=users",
      label: "Usuarios",
      aria: "CRUD public.users",
      group: "Users & Security OPS",
      opsSubGroup: "Identidade",
    },
    {
      to: "/ops/access/security-admin?tab=roles",
      label: "Papeis (user_roles)",
      aria: "Concessao e revogacao de roles",
      group: "Users & Security OPS",
      opsSubGroup: "Identidade",
    },
    {
      to: "/ops/access/security-admin?tab=permissions",
      label: "Grupos de permissao",
      aria: "security_permission_groups memberships",
      group: "Users & Security OPS",
      opsSubGroup: "Identidade",
    },
    {
      to: "/ops/access/security-admin?tab=webhooks",
      label: "Webhooks OPS",
      aria: "Webhook endpoints rotate secret",
      group: "Users & Security OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/ops/access/security-admin?tab=rls-middleware",
      label: "Middleware RLS (JWT · API Key · RBAC)",
      aria: "analytics_service middleware auth api-key rbac",
      group: "Users & Security OPS",
      opsSubGroup: "Autorizacao RLS",
      newTag: "RLS",
    },
    {
      to: "/ops/access/security-admin?tab=rls-session",
      label: "Variaveis sessao PostgreSQL",
      aria: "app.current_tenant_id app.current_user_id app.user_role",
      group: "Users & Security OPS",
      opsSubGroup: "Autorizacao RLS",
      newTag: "RLS",
    },
    {
      to: "/ops/access/security-admin?tab=api-keys",
      label: "API keys · rotacao",
      aria: "security_api_keys rotate",
      group: "Users & Security OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/ops/access/security-admin?tab=critical-tables",
      label: "Tabelas criticas · registry",
      aria: "users privacy_consents audit_logs sem RLS APPLICATION",
      group: "Users & Security OPS",
      opsSubGroup: "Camada aplicacao",
      newTag: "App",
    },
    {
      to: "/ops/access/security-admin?tab=critical-policies",
      label: "Politicas role x operacao",
      aria: "app_critical_table_policy",
      group: "Users & Security OPS",
      opsSubGroup: "Camada aplicacao",
      newTag: "App",
    },
    {
      to: "/ops/access/security-admin?tab=critical-access-log",
      label: "Log decisoes de acesso",
      aria: "ALLOWED DENIED app_critical_table_access_log",
      group: "Users & Security OPS",
      opsSubGroup: "Camada aplicacao",
    },
    {
      to: "/ops/access/security-admin?tab=critical-audit-public",
      label: "audit_logs publico",
      aria: "public.audit_logs imutavel source_service",
      group: "Users & Security OPS",
      opsSubGroup: "Camada aplicacao",
      newTag: "App",
    },
    {
      to: "/ops/access/security-admin?tab=audit",
      label: "Auditoria (security_audit_logs)",
      aria: "security_audit_logs",
      group: "Users & Security OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/ops/access/security-admin?tab=cross-domain",
      label: "Vinculos cross-domain",
      aria: "user_domain_links partner marketplace locker",
      group: "Users & Security OPS",
      opsSubGroup: "Cross-domain",
    },
    {
      to: "/ops/access/user-roles",
      label: "Papeis (legado)",
      aria: "Tela legada user_roles",
      group: "Users & Security OPS",
      opsSubGroup: "Legado",
    },
    {
      to: "/ops/payment-gateway/admin",
      label: "Payment Gateway — catalogo e PSP",
      aria: "Metodos de pagamento, PSP, webhook, API key, device registry e risk",
      group: "Cadastros OPS",
      opsSubGroup: "Payment Gateway",
    },
    {
      to: "/ops/hardware/admin?tab=dashboard",
      label: "Hardware — dashboard 360°",
      aria: "Visao cross-domain hardware marketplace payment carriers finance",
      group: "Hardware OPS",
      opsSubGroup: "Hub",
      newTag: "Hub",
    },
    {
      to: "/ops/hardware/admin?tab=vendors",
      label: "Hardware — redes / vendors",
      aria: "SwipBox Cleveron Pickup PL webhook API key",
      group: "Hardware OPS",
      opsSubGroup: "Hub",
    },
    {
      to: "/ops/hardware/admin?tab=ecosystem",
      label: "Hardware — ecossistema mundial",
      aria: "InPost DPD Magalu Mercado Livre Amazon players",
      group: "Hardware OPS",
      opsSubGroup: "Cross-domain",
    },
    {
      to: "/ops/hardware/admin?tab=marketplace",
      label: "Hardware — marketplace ↔ locker",
      aria: "seller_locker_network_links Magalu Mercado Livre",
      group: "Hardware OPS",
      opsSubGroup: "Cross-domain",
    },
    {
      to: "/ops/hardware/admin?tab=payments",
      label: "Hardware — payment ↔ locker",
      aria: "locker payment methods PSP PIX cartao",
      group: "Hardware OPS",
      opsSubGroup: "Cross-domain",
    },
    {
      to: "/ops/hardware/admin?tab=carriers",
      label: "Hardware — carriers globais",
      aria: "InPost DPD DHL USPS Correios",
      group: "Hardware OPS",
      opsSubGroup: "Cross-domain",
    },
    {
      to: "/ops/hardware/admin?tab=channels",
      label: "Hardware — integration hub",
      aria: "food delivery agregadores PUDO channel bindings",
      group: "Hardware OPS",
      opsSubGroup: "Cross-domain",
      newTag: "Hub",
    },
    {
      to: "/ops/hardware/admin?tab=world",
      label: "Hardware — World Ops · certificacoes",
      aria: "Certificacoes corredores SLA webhook DLQ replay mirror marketplace",
      group: "Hardware OPS",
      opsSubGroup: "Professional Ops",
      newTag: "Pro",
    },
    {
      to: "/ops/hardware/admin?tab=references",
      label: "Hardware — refs outros dominios",
      aria: "ORDER_PICKUP RUNTIME FINANCE MARKETPLACE",
      group: "Hardware OPS",
      opsSubGroup: "Cross-domain",
    },
    {
      to: "/ops/hardware/admin?tab=links",
      label: "Hardware — Locker 360 cross-domain",
      aria: "Payment gateway order pickup payments finance partner gaps sync",
      group: "Hardware OPS",
      opsSubGroup: "Cross-domain",
      newTag: "New",
    },
    {
      to: "/ops/hardware/admin?tab=assets",
      label: "Hardware — ativos CAPEX",
      aria: "ellanlab_hardware_assets depreciacao CAPEX",
      group: "Hardware OPS",
      opsSubGroup: "Financeiro",
    },
    {
      to: "/ops/hardware/admin?tab=finance",
      label: "Hardware — CAPEX / OPEX",
      aria: "locker_capex locker_opex ROI",
      group: "Hardware OPS",
      opsSubGroup: "Financeiro",
    },
    {
      to: "/ops/hardware/admin?tab=operators",
      label: "Hardware — operadores de rede",
      aria: "DPD USPS DHL InPost locker operators",
      group: "Hardware OPS",
      opsSubGroup: "Operadores",
    },
    {
      to: "/ops/hardware/admin?tab=runtime",
      label: "Hardware — runtime MQTT",
      aria: "runtime_lockers topology mqtt",
      group: "Hardware OPS",
      opsSubGroup: "Runtime",
    },
    {
      to: "/ops/hardware/admin?tab=topology",
      label: "Hardware — features / slots",
      aria: "runtime_locker_features runtime_locker_slots",
      group: "Hardware OPS",
      opsSubGroup: "Runtime",
    },
    {
      to: "/ops/hardware/admin?tab=ops",
      label: "Hardware — devices e telemetria",
      aria: "device registry sync queue telemetry",
      group: "Hardware OPS",
      opsSubGroup: "Operacoes",
    },
    {
      to: "/ops/payments/admin",
      label: "Centro de comando (KPIs)",
      aria: "Resumo PAYMENT, prontidao global, simulador roteamento",
      group: "Payments OPS",
      opsSubGroup: "Hub",
      newTag: "Hub",
      opsSearch: "intelligence readiness kpi",
    },
    {
      to: "/ops/payments/admin?tab=graph",
      label: "Grafo ecossistema",
      aria: "React Flow players e relacoes mundiais",
      group: "Payments OPS",
      opsSubGroup: "Hub",
      newTag: "Flow",
      opsSearch: "inpost dhl flow",
    },
    {
      to: "/ops/payments/admin?tab=cross-domain",
      label: "Hub 360° · gaps",
      aria: "Registry domínios, refs externas, obrigações, order-360",
      group: "Payments OPS",
      opsSubGroup: "Cross-domain",
      newTag: "New",
      opsSearch: "finance fiscal marketplace obligation",
    },
    {
      to: "/ops/payments/admin?tab=order-context",
      label: "Contexto pedido",
      aria: "payment_order_context tenant locker marketplace carrier",
      group: "Payments OPS",
      opsSubGroup: "Cross-domain",
      opsSearch: "order context",
    },
    {
      to: "/ops/payments/admin?tab=ecosystem",
      label: "Players mundiais",
      aria: "InPost, DHL, Magalu, Mercado Livre, Amazon, Correios, CTT",
      group: "Payments OPS",
      opsSubGroup: "Mundial",
      opsSearch: "ecosystem carrier locker",
    },
    {
      to: "/ops/payments/admin?tab=segments",
      label: "Segmentos",
      aria: "LOCKER_NETWORK CARRIER MARKETPLACE FOOD_DELIVERY",
      group: "Payments OPS",
      opsSubGroup: "Mundial",
    },
    {
      to: "/ops/payments/admin?tab=integrations",
      label: "Integrações · playbook",
      aria: "Readiness score sandbox producao",
      group: "Payments OPS",
      opsSubGroup: "Mundial",
    },
    {
      to: "/ops/payments/admin?tab=coverage",
      label: "Cobertura por país",
      aria: "payment_player_country_coverage",
      group: "Payments OPS",
      opsSubGroup: "Mundial",
      opsSearch: "br pt es country",
    },
    {
      to: "/ops/payments/admin?tab=relations",
      label: "Relações entre players",
      aria: "CHANNEL_USES_CARRIER WHITE_LABEL AGGREGATES",
      group: "Payments OPS",
      opsSubGroup: "Mundial",
    },
    {
      to: "/ops/payments/admin?tab=milestones",
      label: "Roadmap integração",
      aria: "Marcos DISCOVERY a PRODUCTION CRUD",
      group: "Payments OPS",
      opsSubGroup: "Valor",
      newTag: "CRUD",
    },
    {
      to: "/ops/payments/admin?tab=routing",
      label: "Roteamento PSP",
      aria: "Regras pais metodo PSP primario fallback CRUD",
      group: "Payments OPS",
      opsSubGroup: "Valor",
      newTag: "CRUD",
      opsSearch: "psp stripe adyen",
    },
    {
      to: "/ops/payments/admin?tab=corridors",
      label: "Corredores FX",
      aria: "Settlement cross-border BR PT CN US",
      group: "Payments OPS",
      opsSubGroup: "Valor",
    },
    {
      to: "/ops/payments/admin?tab=compliance",
      label: "Compliance",
      aria: "LGPD GDPR PCI risk tier",
      group: "Payments OPS",
      opsSubGroup: "Valor",
    },
    {
      to: "/ops/payments/admin?tab=incidents",
      label: "Incidentes",
      aria: "SLA webhook latency rate limit",
      group: "Payments OPS",
      opsSubGroup: "Valor",
    },
    {
      to: "/ops/payments/admin?tab=transactions",
      label: "Transações",
      aria: "payment_transactions",
      group: "Payments OPS",
      opsSubGroup: "Ledger",
    },
    {
      to: "/ops/payments/admin?tab=instructions",
      label: "Instruções PIX / boleto",
      aria: "payment_instructions QR",
      group: "Payments OPS",
      opsSubGroup: "Ledger",
      opsSearch: "pix boleto",
    },
    {
      to: "/ops/payments/admin?tab=splits",
      label: "Splits repasse",
      aria: "payment_splits marketplace carrier",
      group: "Payments OPS",
      opsSubGroup: "Ledger",
    },
    {
      to: "/ops/payments/admin?tab=payments",
      label: "Ledger payments",
      aria: "Tabela payments provider status",
      group: "Payments OPS",
      opsSubGroup: "Ledger",
    },
    {
      to: "/ops/payments/admin?tab=batches",
      label: "Lotes conciliação",
      aria: "payment_reconciliation_batch",
      group: "Payments OPS",
      opsSubGroup: "Conciliação",
    },
    {
      to: "/ops/payments/reconciliation",
      label: "Workbench conciliação",
      aria: "Conciliação payment_transactions e payment_splits",
      group: "Payments OPS",
      opsSubGroup: "Conciliação",
      opsSearch: "reconcile status lote",
    },
    {
      to: "/ops/payments/admin?tab=webhooks",
      label: "Webhooks",
      aria: "webhook_endpoints rotate secret",
      group: "Payments OPS",
      opsSubGroup: "Integração",
    },
    {
      to: "/ops/payments/admin?tab=deliveries",
      label: "Entregas · DLQ",
      aria: "webhook_deliveries retry",
      group: "Payments OPS",
      opsSubGroup: "Integração",
    },
    {
      to: "/ops/payments/admin?tab=events",
      label: "Gateway events",
      aria: "gateway_events auditoria runtime",
      group: "Payments OPS",
      opsSubGroup: "Integração",
    },
    {
      to: "/ops/payments/admin?tab=holds",
      label: "Holds parceiro",
      aria: "partner_payment_holds finance",
      group: "Payments OPS",
      opsSubGroup: "Financeiro",
    },
    {
      to: "/ops/payments/admin?tab=vault",
      label: "Cartões salvos",
      aria: "saved_payment_methods vault",
      group: "Payments OPS",
      opsSubGroup: "Vault",
    },
    {
      to: "/ops/money-cambio/admin",
      label: "Money & Cambio — visao global",
      aria: "Dashboard KPIs, grade de prontidao e cobertura mundial",
      group: "Money OPS",
      opsSubGroup: "Hub",
      newTag: "Hub",
    },
    {
      to: "/ops/money-cambio/admin?tab=players",
      label: "Money — players ecossistema",
      aria: "Lockers, carriers, marketplaces, coleta, food delivery — ligação Finance/Fiscal",
      group: "Money OPS",
      opsSubGroup: "Ecossistema",
      newTag: "New",
    },
    {
      to: "/ops/money-cambio/admin?tab=segments",
      label: "Money — segmentos",
      aria: "Taxonomia LOCKER_NETWORK, CARRIER, MARKETPLACE, FOOD_DELIVERY…",
      group: "Money OPS",
      opsSubGroup: "Ecossistema",
    },
    {
      to: "/ops/money-cambio/admin?tab=relations",
      label: "Money — relacoes players",
      aria: "Grafo WHITE_LABEL, AGGREGATES, CHANNEL_USES_CARRIER…",
      group: "Money OPS",
      opsSubGroup: "Ecossistema",
    },
    {
      to: "/ops/money-cambio/admin?tab=intelligence",
      label: "Money — intelligence",
      aria: "Readiness score, insights, gaps fiscal/FX, alertas",
      group: "Money OPS",
      opsSubGroup: "Intelligence",
      newTag: "New",
    },
    {
      to: "/ops/money-cambio/admin?tab=countries",
      label: "Money — paises operacionais",
      aria: "money_operating_country, redes locker e zona regulatoria",
      group: "Money OPS",
      opsSubGroup: "Mundial",
    },
    {
      to: "/ops/money-cambio/admin?tab=matrix",
      label: "Money — metodo x pais",
      aria: "money_method_country_matrix",
      group: "Money OPS",
      opsSubGroup: "Mundial",
    },
    {
      to: "/ops/money-cambio/admin?tab=aliases",
      label: "Money — aliases UI",
      aria: "payment_method_ui_alias",
      group: "Money OPS",
      opsSubGroup: "Catalogo",
    },
    {
      to: "/ops/money-cambio/admin?tab=currencies",
      label: "Money — moedas ISO",
      aria: "money_currency_catalog",
      group: "Money OPS",
      opsSubGroup: "Catalogo",
    },
    {
      to: "/ops/money-cambio/admin?tab=methods",
      label: "Money — metodos de pagamento",
      aria: "payment_method_catalog",
      group: "Money OPS",
      opsSubGroup: "Catalogo",
    },
    {
      to: "/ops/money-cambio/admin?tab=interfaces",
      label: "Money — interfaces (totem, app)",
      aria: "payment_interface_catalog",
      group: "Money OPS",
      opsSubGroup: "Catalogo",
    },
    {
      to: "/ops/money-cambio/admin?tab=wallets",
      label: "Money — wallet providers",
      aria: "wallet_provider_catalog",
      group: "Money OPS",
      opsSubGroup: "Wallets",
    },
    {
      to: "/ops/money-cambio/admin?tab=corridors",
      label: "Cambio — corredores pagamento",
      aria: "cambio_payment_corridor cross-border",
      group: "Cambio OPS",
      opsSubGroup: "Corredores",
    },
    {
      to: "/ops/money-cambio/admin?tab=fx",
      label: "Cambio — taxas FX",
      aria: "cambio_fx_rates e conversao",
      group: "Cambio OPS",
      opsSubGroup: "Taxas",
    },
    {
      to: "/ops/money-cambio/admin?tab=compliance",
      label: "Cambio — limites AML/KYC",
      aria: "money_compliance_limit",
      group: "Cambio OPS",
      opsSubGroup: "Compliance",
    },
    {
      to: "/ops/money-cambio/admin?tab=audit",
      label: "Cambio — auditoria FX",
      aria: "cambio_fx_rate_audit",
      group: "Cambio OPS",
      opsSubGroup: "Auditoria",
    },
    {
      to: "/ops/money-cambio/admin?tab=settlements",
      label: "Cambio — calendario settlement",
      aria: "money_settlement_schedule T+N, cut-off UTC por player/corredor",
      group: "Cambio OPS",
      opsSubGroup: "Settlement",
      newTag: "New",
    },
    {
      to: "/ops/money-cambio/admin?tab=pricing",
      label: "Cambio — simulador cotacao",
      aria: "Preview FX + spread + markup + compliance + settlement",
      group: "Cambio OPS",
      opsSubGroup: "Pricing",
      newTag: "New",
    },
    {
      to: "/ops/money-cambio/admin?tab=fxlocks",
      label: "Cambio — travas FX",
      aria: "money_fx_lock hedge operacional",
      group: "Cambio OPS",
      opsSubGroup: "Pricing",
    },
    {
      to: "/ops/money-cambio/admin?tab=treasury",
      label: "Money — tesouraria FX",
      aria: "Exposicao por moeda, gaps e locks ativos",
      group: "Money OPS",
      opsSubGroup: "Tesouraria",
      newTag: "New",
    },
    {
      to: "/ops/money-cambio/admin?tab=rails",
      label: "Money — payment rails",
      aria: "Metodos e wallets habilitados por player e pais",
      group: "Money OPS",
      opsSubGroup: "Rails",
      newTag: "New",
    },
    {
      to: "/ops/money-cambio/admin?tab=partners",
      label: "Cambio — parceiros FX",
      aria: "Integracao, webhook e API key",
      group: "Cambio OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/ops/fiscal/admin?tab=global",
      label: "Fiscal OPS — Global (jurisdicoes · KPIs)",
      aria: "Jurisdicoes BR PT ES DE US, resumo global e corredores",
      group: "Fiscal OPS",
      opsSubGroup: "Global",
      newTag: "Hub",
    },
    {
      to: "/ops/fiscal/admin?tab=intelligence",
      label: "Fiscal OPS — inteligencia",
      aria: "Scan insights, certificados expirando, contingencia SEFAZ, webhook DLQ",
      group: "Fiscal OPS",
      opsSubGroup: "Inteligencia",
      newTag: "New",
    },
    {
      to: "/ops/fiscal/admin",
      label: "Fiscal OPS — emissores e integracao",
      aria: "Emissores fiscais, webhook, API key rotation",
      group: "Fiscal OPS",
      opsSubGroup: "Emissores",
    },
    {
      to: "/ops/fiscal/admin?tab=corridors",
      label: "Fiscal OPS — corredores mundiais",
      aria: "fiscal_tax_corridors BR-BR, BR-PT, PT-ES, regras ICMS/IVA",
      group: "Fiscal OPS",
      opsSubGroup: "Corredores",
    },
    {
      to: "/ops/fiscal/admin?tab=readiness",
      label: "Fiscal OPS — prontidao",
      aria: "Score A-D por emissor, certificados e API",
      group: "Fiscal OPS",
      opsSubGroup: "Prontidao",
    },
    {
      to: "/ops/fiscal/admin?tab=certifications",
      label: "Fiscal OPS — certificacoes",
      aria: "A1 ICP-Brasil, LGPD, SAF-T, NFC-e homolog",
      group: "Fiscal OPS",
      opsSubGroup: "Compliance",
    },
    {
      to: "/ops/fiscal/admin?tab=documents",
      label: "Fiscal OPS — documentos",
      aria: "fiscal_documents NFC-e e comprovantes",
      group: "Fiscal OPS",
      opsSubGroup: "Documentos",
    },
    {
      to: "/ops/fiscal/admin?tab=classification",
      label: "Fiscal OPS — NCM / CFOP",
      aria: "Regras e log de classificacao automatica",
      group: "Fiscal OPS",
      opsSubGroup: "Classificacao",
    },
    {
      to: "/ops/fiscal/admin?tab=gaps",
      label: "Fiscal OPS — reconciliacao",
      aria: "fiscal_reconciliation_gaps e resolucao",
      group: "Fiscal OPS",
      opsSubGroup: "Gaps",
    },
    {
      to: "/ops/fiscal/admin?tab=slo",
      label: "Fiscal OPS — SLA emissao",
      aria: "fiscal_emission_slo_policies p99 e success rate",
      group: "Fiscal OPS",
      opsSubGroup: "SLA",
    },
    {
      to: "/ops/fiscal/admin?tab=webhooks",
      label: "Fiscal OPS — webhook DLQ",
      aria: "fiscal_webhook_delivery_log falhas e retries",
      group: "Fiscal OPS",
      opsSubGroup: "Webhooks",
    },
    {
      to: "/ops/fiscal/admin?tab=config",
      label: "Fiscal OPS — tenant e SKU",
      aria: "tenant_fiscal_config, product_fiscal_config e provider health",
      group: "Fiscal OPS",
      opsSubGroup: "Config",
    },
    {
      to: "/ops/fiscal/admin?tab=governance",
      label: "Fiscal OPS — governanca",
      aria: "fiscal_accounting_approvals e fiscal_authority_callbacks",
      group: "Fiscal OPS",
      opsSubGroup: "Governanca",
    },
    {
      to: "/ops/finance/admin?tab=networks",
      label: "Finance — redes mundiais",
      aria: "Catálogo 90+ players, world-priority-index e guia Como integrar por player",
      group: "Finance OPS — Global",
      opsSubGroup: "Catálogo",
      newTag: "Global",
    },
    {
      to: "/ops/finance/admin?tab=intelligence",
      label: "Finance — inteligencia",
      aria: "Ecosystem Intelligence: scan, insights, benchmarks, health checks e resolver",
      group: "Finance OPS — Global",
      opsSubGroup: "Inteligência",
      newTag: "New",
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
      to: "/financial",
      label: "Financial — dashboard executivo",
      aria: "v_financial_dashboard KPIs executivos",
      group: "Financial",
      opsSubGroup: "Executivo",
      newTag: "CFO",
    },
    {
      to: "/financial/locker-pnl",
      label: "Financial — P&L locker",
      aria: "mv_locker_monthly_pnl rentabilidade",
      group: "Financial",
      opsSubGroup: "Executivo",
    },
    {
      to: "/financial/expansion",
      label: "Financial — simulador expansão",
      aria: "simulate_expansion_scenario_v2",
      group: "Financial",
      opsSubGroup: "Executivo",
    },
    {
      to: "/financial/partners",
      label: "Financial — settlements parceiro",
      aria: "partner_revenue_monthly e settlement_batches",
      group: "Financial",
      opsSubGroup: "Executivo",
    },
    {
      to: "/ops/analytics/financial",
      label: "Analytics financeiro",
      aria: "mv_locker_monthly_profitability, v_financial_dashboard e mv_realtime_kpis",
      group: "Finance OPS",
      opsSubGroup: "PnL",
      newTag: "MV",
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
      to: "/ops/orders/admin?tab=overview",
      label: "Pedidos OPS — hub KPIs",
      aria: "Hub KPIs pedidos pickups outbox omnichannel fulfillment timeline SLA disputes",
      group: "Pedidos OPS",
      opsSubGroup: "Hub",
      newTag: "Hub",
    },
    {
      to: "/ops/orders/admin?tab=lookup",
      label: "Pedidos OPS — Order 360",
      aria: "timeline health score risk flags consolidated lookup",
      group: "Pedidos OPS",
      opsSubGroup: "Hub",
      newTag: "360",
    },
    {
      to: "/ops/orders/admin?tab=orders",
      label: "Pedidos OPS — pedidos e pickups",
      aria: "CRUD orders pickups",
      group: "Pedidos OPS",
      opsSubGroup: "Nucleo",
    },
    {
      to: "/ops/orders/admin?tab=items",
      label: "Pedidos OPS — itens SKU",
      aria: "order_items CRUD",
      group: "Pedidos OPS",
      opsSubGroup: "Nucleo",
    },
    {
      to: "/ops/orders/admin?tab=substitutions",
      label: "Pedidos OPS — substituicoes SKU",
      aria: "order_item_substitutions OUT_OF_STOCK",
      group: "Pedidos OPS",
      opsSubGroup: "Nucleo",
      newTag: "P7+",
    },
    {
      to: "/ops/orders/admin?tab=gifts",
      label: "Pedidos OPS — gift recipient",
      aria: "order_gift_pickup authorization third party",
      group: "Pedidos OPS",
      opsSubGroup: "Nucleo",
      newTag: "P7+",
    },
    {
      to: "/ops/orders/admin?tab=allocations",
      label: "Pedidos OPS — alocacoes slot",
      aria: "allocations locker slot state",
      group: "Pedidos OPS",
      opsSubGroup: "Nucleo",
    },
    {
      to: "/ops/orders/admin?tab=channels",
      label: "Pedidos OPS — players (28)",
      aria: "P3 P4 InPost DHL Magalu aggregators locker networks",
      group: "Pedidos OPS",
      opsSubGroup: "Canais",
    },
    {
      to: "/ops/orders/admin?tab=food",
      label: "Pedidos OPS — food delivery",
      aria: "iFood Rappi Uber Eats Glovo DoorDash locker handoff",
      group: "Pedidos OPS",
      opsSubGroup: "Canais",
    },
    {
      to: "/ops/orders/admin?tab=omnichannel",
      label: "Pedidos OPS — omnichannel",
      aria: "Magalu Mercado Livre Corte Ingles store pickup locker",
      group: "Pedidos OPS",
      opsSubGroup: "Canais",
    },
    {
      to: "/ops/orders/admin?tab=warehouse",
      label: "Pedidos OPS — fulfillment CD",
      aria: "DHL DPD Correios CTT fulfillment_orders",
      group: "Pedidos OPS",
      opsSubGroup: "Canais",
    },
    {
      to: "/ops/orders/admin?tab=manifests",
      label: "Pedidos OPS — manifestos logistica",
      aria: "logistics_manifests DPD Correios CTT",
      group: "Pedidos OPS",
      opsSubGroup: "Logistica",
    },
    {
      to: "/ops/orders/admin?tab=deadlines",
      label: "Pedidos OPS — lifecycle deadlines",
      aria: "PICKUP_TIMEOUT PREPAYMENT lifecycle-deadlines",
      group: "Pedidos OPS",
      opsSubGroup: "Logistica",
    },
    {
      to: "/ops/orders/admin?tab=sla",
      label: "Pedidos OPS — SLA watches",
      aria: "sla breach deadline sync watches",
      group: "Pedidos OPS",
      opsSubGroup: "Logistica",
    },
    {
      to: "/ops/orders/admin?tab=disputes",
      label: "Pedidos OPS — disputas",
      aria: "chargeback dispute open amount",
      group: "Pedidos OPS",
      opsSubGroup: "Risco",
    },
    {
      to: "/ops/orders/admin?tab=returns",
      label: "Pedidos OPS — devolucoes RMA",
      aria: "order_returns locker drop off refund",
      group: "Pedidos OPS",
      opsSubGroup: "Risco",
      newTag: "P7",
    },
    {
      to: "/ops/orders/admin?tab=holds",
      label: "Pedidos OPS — holds OPS",
      aria: "order_ops_holds fraud review block",
      group: "Pedidos OPS",
      opsSubGroup: "Risco",
      newTag: "P7",
    },
    {
      to: "/ops/orders/admin?tab=notifications",
      label: "Pedidos OPS — notificacoes",
      aria: "SMS email push pickup reminder",
      group: "Pedidos OPS",
      opsSubGroup: "Comunicacao",
      newTag: "P7",
    },
    {
      to: "/ops/orders/admin?tab=payments",
      label: "Pedidos OPS — transacoes gateway",
      aria: "payment_transactions mirror sync",
      group: "Pedidos OPS",
      opsSubGroup: "Comunicacao",
      newTag: "P7+",
    },
    {
      to: "/ops/orders/admin?tab=reconciliation",
      label: "Pedidos OPS — reconciliacao pagamento",
      aria: "payment reconciliation gateway captured expected",
      group: "Pedidos OPS",
      opsSubGroup: "Comunicacao",
      newTag: "P7",
    },
    {
      to: "/ops/payments/admin?tab=transactions",
      label: "Pedidos OPS — payments-admin tx",
      aria: "cross link payments admin transactions",
      group: "Pedidos OPS",
      opsSubGroup: "Comunicacao",
    },
    {
      to: "/ops/orders/admin?tab=commissions",
      label: "Pedidos OPS — comissoes marketplace",
      aria: "marketplace_commissions",
      group: "Pedidos OPS",
      opsSubGroup: "Marketplace",
    },
    {
      to: "/ops/orders/admin?tab=credits",
      label: "Pedidos OPS — creditos",
      aria: "credits goodwill refund",
      group: "Pedidos OPS",
      opsSubGroup: "Marketplace",
    },
    {
      to: "/ops/orders/admin?tab=partners",
      label: "Pedidos OPS — parceiros e webhook",
      aria: "ecommerce logistics webhook api key rotate",
      group: "Pedidos OPS",
      opsSubGroup: "Parceiros",
    },
    {
      to: "/ops/orders/admin?tab=integration",
      label: "Pedidos OPS — outbox e health",
      aria: "partner_outbox domain_event integration_health replay",
      group: "Pedidos OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/ops/integration/orders-fiscal",
      label: "Pedidos OPS — I-1 fiscal",
      aria: "fulfillment partner-events por order_id",
      group: "Pedidos OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/ops/integration/orders-partner-lookup",
      label: "Pedidos OPS — L-3 partner lookup",
      aria: "lookup dedicado partner ref order",
      group: "Pedidos OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/ops/workers/admin?tab=lifecycle",
      label: "Pedidos OPS — workers lifecycle",
      aria: "workers lifecycle_deadlines queue",
      group: "Pedidos OPS",
      opsSubGroup: "Workers",
    },
    {
      to: "/ops/workers/admin?tab=domain",
      label: "Pedidos OPS — workers domain outbox",
      aria: "workers domain_event_outbox",
      group: "Pedidos OPS",
      opsSubGroup: "Workers",
    },
    {
      to: "/ops/order-pickup/admin",
      label: "Pedidos OPS — URL legada pickup",
      aria: "Alias legado order-pickup admin",
      group: "Pedidos OPS",
      opsSubGroup: "Legado",
    },
    {
      to: "/ops/order/deadlines",
      label: "Pedidos OPS — lifecycle interno",
      aria: "order_lifecycle_service POST internal deadlines",
      group: "Pedidos OPS",
      opsSubGroup: "Legado",
    },
    {
      to: "/ops/workers/admin",
      label: "Workers PostgreSQL — visao geral",
      aria: "Node workers domain_event_outbox lifecycle_deadlines inventory_sync_queue DLQ",
      group: "Cadastros OPS",
      opsSubGroup: "Workers",
      newTag: "Node",
    },
    {
      to: "/ops/workers/admin?tab=domain",
      label: "Workers — domain event outbox",
      aria: "Webhook parceiros domain_event_outbox PENDING PUBLISHED",
      group: "Cadastros OPS",
      opsSubGroup: "Workers",
    },
    {
      to: "/ops/workers/admin?tab=lifecycle",
      label: "Workers — lifecycle deadlines",
      aria: "PREPAYMENT_TIMEOUT POSTPAYMENT_EXPIRY PICKUP_TIMEOUT",
      group: "Cadastros OPS",
      opsSubGroup: "Workers",
    },
    {
      to: "/ops/workers/admin?tab=inventory",
      label: "Workers — sync estoque marketplaces",
      aria: "Shopee Magalu Mercado Livre inventory_sync_queue",
      group: "Cadastros OPS",
      opsSubGroup: "Workers",
    },
    {
      to: "/ops/workers/admin?tab=dlq",
      label: "Workers — dead letter queue",
      aria: "worker_dead_letter_queue falhas permanentes",
      group: "Cadastros OPS",
      opsSubGroup: "Workers",
    },
    {
      to: "/ops/marketplace/admin?tab=overview",
      label: "Marketplace — visao geral",
      aria: "Dashboard KPIs, sellers, catalogo, comissoes, repasses, KYC e disputas",
      group: "Marketplace OPS",
      opsSubGroup: "Visao geral",
      newTag: "Hub",
    },
    {
      to: "/ops/marketplace/admin?tab=sellers",
      label: "Marketplace — sellers",
      aria: "Onboarding sellers, status e vinculos",
      group: "Marketplace OPS",
      opsSubGroup: "Nucleo",
    },
    {
      to: "/ops/marketplace/admin?tab=products",
      label: "Marketplace — produtos",
      aria: "Catalogo SKU marketplace",
      group: "Marketplace OPS",
      opsSubGroup: "Nucleo",
    },
    {
      to: "/ops/marketplace/admin?tab=categories",
      label: "Marketplace — categorias",
      aria: "Taxonomia categorias marketplace",
      group: "Marketplace OPS",
      opsSubGroup: "Nucleo",
    },
    {
      to: "/ops/marketplace/admin?tab=channels",
      label: "Marketplace — canais e redes locker",
      aria: "InPost, DHL, Magalu, Mercado Livre, Amazon, DPD, Correios, CTT e vinculos seller",
      group: "Marketplace OPS",
      opsSubGroup: "Canais",
    },
    {
      to: "/ops/marketplace/admin?tab=reviews",
      label: "Marketplace — avaliacoes",
      aria: "Reviews sellers e produtos",
      group: "Marketplace OPS",
      opsSubGroup: "Nucleo",
    },
    {
      to: "/ops/marketplace/admin?tab=readiness",
      label: "Marketplace — prontidao integracao",
      aria: "Score GO_LIVE/PILOT, incidentes e auditoria de sync",
      group: "Marketplace OPS",
      opsSubGroup: "Integracao",
    },
    {
      to: "/ops/workers/admin?tab=inventory",
      label: "Marketplace — sync estoque (workers)",
      aria: "inventory_sync_queue Shopee Magalu Mercado Livre Node worker",
      group: "Marketplace OPS",
      opsSubGroup: "Integracao",
      newTag: "Node",
    },
    {
      to: "/ops/marketplace/admin?tab=readiness",
      label: "Marketplace — Global OPS (corredores · SLA · webhooks)",
      aria: "Certificacoes, corredores internacionais, capability webhooks DLQ replay",
      group: "Marketplace OPS",
      opsSubGroup: "Global OPS",
      newTag: "New",
      opsSearch: "DLQ replay dead-letter seed",
    },
    {
      to: "/ops/marketplace/admin?tab=settlements",
      label: "Marketplace — repasses",
      aria: "Lotes de liquidacao ao seller",
      group: "Marketplace OPS",
      opsSubGroup: "Financeiro",
    },
    {
      to: "/ops/marketplace/admin?tab=payouts",
      label: "Marketplace — contas PIX",
      aria: "Contas de repasse PIX sellers",
      group: "Marketplace OPS",
      opsSubGroup: "Financeiro",
    },
    {
      to: "/ops/marketplace/admin?tab=contacts",
      label: "Marketplace — contatos",
      aria: "Contatos B2B sellers",
      group: "Marketplace OPS",
      opsSubGroup: "Financeiro",
    },
    {
      to: "/ops/marketplace/admin?tab=commissions",
      label: "Marketplace — comissoes",
      aria: "Regras de comissao marketplace",
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
      to: "/ops/marketplace/admin?tab=disputes",
      label: "Marketplace — disputas",
      aria: "Disputas chargeback marketplace",
      group: "Marketplace OPS",
      opsSubGroup: "Compliance",
    },
    {
      to: "/ops/marketplace/admin?tab=integrations",
      label: "Marketplace — webhooks e API keys",
      aria: "seller_webhook_endpoints seller_api_keys rotate",
      group: "Marketplace OPS",
      opsSubGroup: "Integracoes seller",
    },
    {
      to: "/ops/marketplace/admin?tab=audit",
      label: "Marketplace — auditoria sync",
      aria: "marketplace_sync_audit_log readiness channel",
      group: "Marketplace OPS",
      opsSubGroup: "Integracoes seller",
    },
    {
      to: "/ops/marketplace/admin?tab=tiers",
      label: "Marketplace — programas e tiers",
      aria: "STARTER GROWTH ENTERPRISE seller tier enrollment",
      group: "Marketplace OPS",
      opsSubGroup: "Programa global",
    },
    {
      to: "/ops/marketplace/admin?tab=compliance",
      label: "Marketplace — compliance fiscal",
      aria: "IOSS VAT OSS multi-country seller compliance",
      group: "Marketplace OPS",
      opsSubGroup: "Programa global",
    },
    {
      to: "/ops/marketplace/admin?tab=performance",
      label: "Marketplace — performance",
      aria: "GMV OTD defect rate monthly seller KPI",
      group: "Marketplace OPS",
      opsSubGroup: "Programa global",
    },
    {
      to: "/ops/marketplace/admin?tab=agreements",
      label: "Marketplace — contratos",
      aria: "MARKETPLACE_TERMS DATA_PROCESSING agreements",
      group: "Marketplace OPS",
      opsSubGroup: "Programa global",
    },
    {
      to: "/ops/marketplace/admin?tab=risk",
      label: "Marketplace — risco",
      aria: "seller risk assessment fraud chargeback",
      group: "Marketplace OPS",
      opsSubGroup: "Programa global",
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
      label: "Privacy — consentimentos (app layer)",
      aria: "privacy_consents enforcement APPLICATION recorded_by_service",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Camada aplicacao",
      newTag: "App",
    },
    {
      to: "/ops/access/security-admin?tab=critical-policies",
      label: "Privacy — politicas (hub seguranca)",
      aria: "app_critical_table_policy privacy_consents",
      group: "Privacy & Compliance OPS",
      opsSubGroup: "Camada aplicacao",
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
      to: "/cookies",
      label: "Cookies — pagina publica /cookies",
      aria: "Politica de cookies e centro de preferencias",
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
      to: "/ops/orders/admin?tab=deadlines",
      label: "ops /order/deadlines → Pedidos OPS",
      aria: "Lifecycle deadlines listagem order-pickup-admin",
      group: "Order / Pickup",
    },
    {
      to: "/ops/lockers/map",
      label: "Operations — Lockers Map",
      aria: "Mapa Leaflet com status e telemetria live",
      group: "Operations",
      opsSubGroup: "Rede",
      newTag: "Map",
    },
    {
      to: "/ops/maintenance",
      label: "Operations — Maintenance",
      aria: "Kanban de tickets de manutenção",
      group: "Operations",
      opsSubGroup: "Manutenção",
      newTag: "Kanban",
    },
    {
      to: "/ops/noc-alerts",
      label: "Operations — NOC Alerts",
      aria: "Feed vw_noc_alerts em tempo real",
      group: "Operations",
      opsSubGroup: "NOC",
      newTag: "WS",
    },
    {
      to: "/ops/sla-reports",
      label: "Operations — SLA Reports",
      aria: "Relatório SLA breaches",
      group: "Operations",
      opsSubGroup: "SLA",
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
      to: "/ops/subscriptions/admin",
      label: "ops /subscriptions/admin",
      aria: "Hub OPS assinaturas B2C — planos, MRR, benefícios",
      group: "Assinaturas OPS",
      opsSubGroup: "Hub & analytics",
      newTag: "Hub",
    },
    {
      to: "/ops/subscriptions/admin?tab=analytics",
      label: "ops /subscriptions/analytics",
      aria: "Tendências MRR por plano",
      group: "Assinaturas OPS",
      opsSubGroup: "Hub & analytics",
    },
    {
      to: "/ops/subscriptions/admin?tab=ecosystem",
      label: "ops /subscriptions/ecosystem",
      aria: "Players mundiais por tier de assinatura",
      group: "Assinaturas OPS",
      opsSubGroup: "Hub & analytics",
    },
    {
      to: "/ops/subscriptions/admin?tab=plans",
      label: "ops /subscriptions/plans",
      aria: "Planos subscription_plans BASIC PREMIUM PRO ENTERPRISE",
      group: "Assinaturas OPS",
      opsSubGroup: "Planos & catálogo",
    },
    {
      to: "/ops/subscriptions/admin?tab=entitlements",
      label: "ops /subscriptions/entitlements",
      aria: "Entitlements plano x player mundial",
      group: "Assinaturas OPS",
      opsSubGroup: "Planos & catálogo",
    },
    {
      to: "/ops/subscriptions/admin?tab=partners",
      label: "ops /subscriptions/partners",
      aria: "Programas parceiros subscription_partner_programs",
      group: "Assinaturas OPS",
      opsSubGroup: "Planos & catálogo",
    },
    {
      to: "/ops/subscriptions/admin?tab=subscriptions",
      label: "ops /subscriptions/active",
      aria: "Assinaturas customer_subscriptions Magalu InPost DHL 360",
      group: "Assinaturas OPS",
      opsSubGroup: "Operação",
    },
    {
      to: "/ops/subscriptions/admin?tab=benefits",
      label: "ops /subscriptions/benefits",
      aria: "Uso de benefícios subscription_benefits_usage",
      group: "Assinaturas OPS",
      opsSubGroup: "Operação",
    },
    {
      to: "/ops/subscriptions/admin?tab=billing",
      label: "ops /subscriptions/billing",
      aria: "Faturas subscription_invoices",
      group: "Assinaturas OPS",
      opsSubGroup: "Operação",
    },
    {
      to: "/ops/subscriptions/admin?tab=events",
      label: "ops /subscriptions/events",
      aria: "Eventos subscription_events",
      group: "Assinaturas OPS",
      opsSubGroup: "Operação",
    },
    {
      to: "/ops/subscriptions/admin?tab=dunning",
      label: "ops /subscriptions/dunning",
      aria: "Casos dunning inadimplência",
      group: "Assinaturas OPS",
      opsSubGroup: "Operação",
      newTag: "P1",
    },
    {
      to: "/ops/subscriptions/admin?tab=integrations",
      label: "ops /subscriptions/integrations",
      aria: "Webhooks e rotação API keys assinaturas",
      group: "Assinaturas OPS",
      opsSubGroup: "Integrações",
    },
    {
      to: "/ops/subscriptions/admin?tab=deliveries",
      label: "ops /subscriptions/deliveries",
      aria: "Log entregas webhook",
      group: "Assinaturas OPS",
      opsSubGroup: "Integrações",
    },
    {
      to: "/ops/subscriptions/admin?tab=relations",
      label: "ops /subscriptions/relations",
      aria: "Relações player a player subscription_player_relations",
      group: "Assinaturas OPS",
      opsSubGroup: "Integrações",
    },
    {
      to: "/ops/subscriptions/admin?tab=food_delivery",
      label: "ops /subscriptions/food-delivery",
      aria: "Handoffs iFood Rappi Uber Eats",
      group: "Assinaturas OPS",
      opsSubGroup: "Integrações",
    },
    {
      to: "/ops/subscriptions/admin?tab=premium",
      label: "ops /subscriptions/premium",
      aria: "Health churn referrals gifts loyalty experiments renewals",
      group: "Assinaturas OPS",
      opsSubGroup: "Growth",
      newTag: "Pro",
    },
    {
      to: "/ops/subscriptions/admin?tab=global",
      label: "ops /subscriptions/global",
      aria: "Preços regionais add-ons SLA settlements LGPD retenção",
      group: "Assinaturas OPS",
      opsSubGroup: "Growth",
      newTag: "World",
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
    "Operations",
    "Cadastros OPS",
    "Hardware OPS",
    "Payments OPS",
    "ML OPS",
    "Marketplace OPS",
    "Money OPS",
    "Cambio OPS",
    "Privacy & Compliance OPS",
    "Order / Pickup",
    "Lockers",
    "Inteligência",
    "Rentals OPS",
    "Assinaturas OPS",
    "Runtime",
    "Logística",
    "Logística / Inventário",
    "Produtos & Catálogo",
    "Marketing",
    "Billing / Fiscal",
    "Fiscal OPS",
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
                  <OpsMenuPanel
                    groupedOpsLinks={groupedOpsLinks}
                    clusterOpsLinksBySubGroup={clusterOpsLinksBySubGroup}
                    onNavigate={() => setIsOpsMenuOpen(false)}
                  />
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
                    <OpsMenuPanel
                      id="ops-menu-search-mobile"
                      className="mobile-ops-list mobile-ops-list--searchable"
                      variant="mobile"
                      groupedOpsLinks={groupedOpsLinks}
                      clusterOpsLinksBySubGroup={clusterOpsLinksBySubGroup}
                      onNavigate={() => setIsMobileMenuOpen(false)}
                    />
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
            <Route path="/cookies" element={<PublicCookiePolicyPage />} />
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
              path="/ops/lockers/map"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsLockersMapPage />)}
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
              path="/ops/maintenance"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsMaintenanceTicketsPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/noc-alerts"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsNocAlertsPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/sla-reports"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsSlaReportsPage />)}
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
              path="/ops/access/security-admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsUsersSecurityAdminPage />)}
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
              path="/integrations"
              element={
                <OpsRoute>
                  {withBoundary("ops", <IntegrationsShell />)}
                </OpsRoute>
              }
            >
              <Route index element={<Navigate to="/integrations/partners" replace />} />
              <Route path="partners" element={<IntegrationsPartnersList />} />
              <Route path="partners/:partnerId" element={<IntegrationsPartnerDetail />} />
              <Route path="marketplaces" element={<IntegrationsMarketplaces />} />
              <Route path="carriers" element={<IntegrationsCarriers />} />
              <Route path="webhooks" element={<IntegrationsWebhooks />} />
            </Route>
            <Route
              path="/security"
              element={
                <OpsRoute>
                  {withBoundary("ops", <SecurityShell />)}
                </OpsRoute>
              }
            >
              <Route index element={<Navigate to="/security/users" replace />} />
              <Route path="users" element={<SecurityUsersList />} />
              <Route path="users/new" element={<SecurityUserForm />} />
              <Route path="users/:userId" element={<SecurityUserDetail />} />
              <Route path="users/:userId/edit" element={<SecurityUserForm />} />
              <Route path="roles" element={<SecurityRolesList />} />
              <Route path="roles/new" element={<SecurityRoleForm />} />
              <Route path="roles/:roleId" element={<SecurityRoleDetail />} />
              <Route path="roles/:roleId/edit" element={<SecurityRoleForm />} />
              <Route path="permissions" element={<SecurityPermissionsMatrix />} />
              <Route path="api-keys" element={<SecurityApiKeysManager />} />
              <Route path="webhooks" element={<SecurityWebhookConfig />} />
            </Route>
            <Route
              path="/ops/payment-gateway/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsPaymentGatewayAdminPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/hardware/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsHardwareAdminPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/payments/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsPaymentsAdminPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/money-cambio/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsMoneyCambioAdminPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/fiscal/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsFiscalAdminPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/ops/orders/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsOrderPickupAdminPage />)}
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
              path="/ops/workers/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsWorkersAdminPage />)}
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
              path="/ops/analytics/financial"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsFinancialAnalyticsPage />)}
                </OpsRoute>
              }
            />
            <Route
              path="/financial"
              element={
                <OpsRoute>
                  {withBoundary("ops", <FinancialShell />)}
                </OpsRoute>
              }
            >
              <Route index element={<FinancialExecutiveDashboard />} />
              <Route path="locker-pnl" element={<FinancialLockerProfitability />} />
              <Route path="expansion" element={<FinancialExpansionSimulator />} />
              <Route path="partners" element={<FinancialPartnerRevenue />} />
            </Route>
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
              path="/ops/lockers/:id"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsLockerDetailPage />)}
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
              path="/ops/subscriptions/admin"
              element={
                <OpsRoute>
                  {withBoundary("ops", <OpsSubscriptionsAdminPage />)}
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
            to="/cookies" 
            style={{ 
              textDecoration: 'none',
              color: 'inherit',
              transition: 'color var(--transition-base)'
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#667eea'}
            onMouseLeave={(e) => e.currentTarget.style.color = 'inherit'}
          >
            Política de Cookies
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

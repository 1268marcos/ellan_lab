import { lazy, Suspense } from 'react'
import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import PrivateRoute from '../PrivateRoute'
import { useAuth } from '../contexts/AuthContext'
import Dashboard from '../pages/Dashboard'
import Login from '../pages/Login'
import Landing from '../pages/Landing'
import Catalog from '../pages/partners/Catalog'
import Webhooks from '../pages/partners/Webhooks'
import Wallet from '../pages/finance/Wallet'
import Transactions from '../pages/finance/Transactions'
import DashboardMetrics from '../pages/analytics/DashboardMetrics'
import SLOReport from '../pages/analytics/SLOReport'
import Lockers from '../pages/ops/Lockers'
import OpsLockerCreate from '../pages/ops/OpsLockerCreate'
import OpsPartnersAdmin from '../pages/ops/OpsPartnersAdmin'
import OpsUserRoles from '../pages/ops/OpsUserRoles'
import OpsTenantsAdmin from '../pages/ops/OpsTenantsAdmin'
import OpsPaymentGatewayAdmin from '../pages/ops/OpsPaymentGatewayAdmin'
import OpsOrderPickupAdmin from '../pages/ops/OpsOrderPickupAdmin'
import OpsMarketplaceAdmin from '../pages/ops/OpsMarketplaceAdmin'
import OpsFinanceAdmin from '../pages/ops/OpsFinanceAdmin'
import OpsPrivacyComplianceAdmin from '../pages/ops/OpsPrivacyComplianceAdmin'
import OpsRentalAdmin from '../pages/ops/OpsRentalAdmin'
import OpsMlAdmin from '../pages/ops/OpsMlAdmin'
import OpsProductsAdmin from '../pages/ops/OpsProductsAdmin'
import OpsProductsCatalog from '../pages/ops/OpsProductsCatalog'
import OpsProductCategories from '../pages/ops/OpsProductCategories'
import OpsProductAssets from '../pages/ops/OpsProductAssets'
import OpsPromotionsAdmin from '../pages/ops/OpsPromotionsAdmin'
import Manifests from '../pages/ops/Manifests'
import Compatibility from '../pages/intelligence/Compatibility'
import PredictiveHealth from '../pages/intelligence/PredictiveHealth'
import OccupancyForecast from '../pages/intelligence/OccupancyForecast'
import FeedbackInsights from '../pages/intelligence/FeedbackInsights'
import Reconcile from '../pages/fiscal/Reconcile'
import Profile from '../pages/settings/Profile'
import NotFound from '../pages/NotFound'
import PrivacyPolicy from '../pages/legal/PrivacyPolicy'
import TermsOfUse from '../pages/legal/TermsOfUse'
import SupportCenter from '../pages/support/SupportCenter'

const BillingCycles = lazy(() => import('../pages/finance/BillingCycles'))
const PartnerInvoices = lazy(() => import('../pages/finance/PartnerInvoices'))
const CreditNotes = lazy(() => import('../pages/finance/CreditNotes'))
const Disputes = lazy(() => import('../pages/finance/Disputes'))
const LifecycleMetrics = lazy(() => import('../pages/lifecycle/Metrics'))
const LifecycleRanking = lazy(() => import('../pages/lifecycle/Ranking'))
const LifecycleHealth = lazy(() => import('../pages/lifecycle/Health'))
const RuntimeDashboard = lazy(() => import('../pages/runtime/Dashboard'))
const RuntimeAllocations = lazy(() => import('../pages/runtime/Allocations'))
const OpsLockerStatus = lazy(() => import('../pages/partners/OpsLockerStatus'))
const OpsPickupFlow = lazy(() => import('../pages/partners/OpsPickupFlow'))

const financeLazyFallback = (
  <div className="p-6 text-center text-sm text-slate-400">Carregando...</div>
)

const lifecycleLazyFallback = (
  <div className="p-6 text-center text-sm text-slate-400">Carregando ciclo de vida...</div>
)

const runtimeLazyFallback = (
  <div className="p-6 text-center text-sm text-slate-400">Carregando runtime…</div>
)

const opsPartnersLazyFallback = (
  <div className="p-6 text-center text-sm text-slate-400">Carregando operacional...</div>
)

function Protected({ children }: { children: JSX.Element }) {
  return (
    <PrivateRoute>
      {children}
    </PrivateRoute>
  )
}

function IntelligenceOutlet() {
  return <Outlet />
}

function AccessDenied() {
  return (
    <div className="p-6 text-center text-sm text-red-400">
      Acesso Negado
    </div>
  )
}

function OpsOnly({ children }: { children: JSX.Element }) {
  const { profile } = useAuth()
  if (profile !== 'admin' && profile !== 'ops') {
    return <AccessDenied />
  }
  return children
}

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/legal/privacy" element={<PrivacyPolicy />} />
      <Route path="/legal/terms" element={<TermsOfUse />} />
      <Route path="/support" element={<SupportCenter />} />
      <Route path="/login" element={<Login />} />

      <Route path="/dashboard" element={<Navigate to="/dashboard/admin" replace />} />
      <Route path="/dashboard/admin" element={<Protected><Dashboard /></Protected>} />
      <Route path="/dashboard/partner" element={<Protected><Catalog /></Protected>} />
      <Route path="/dashboard/ops" element={<Protected><Lockers /></Protected>} />
      <Route path="/partners/catalog" element={<Protected><Catalog /></Protected>} />
      <Route path="/partners/webhooks" element={<Protected><Webhooks /></Protected>} />
      <Route
        path="/partners/ops/lockers"
        element={
          <Protected>
            <OpsOnly>
              <Suspense fallback={opsPartnersLazyFallback}>
                <OpsLockerStatus />
              </Suspense>
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/partners/ops/pickups"
        element={
          <Protected>
            <OpsOnly>
              <Suspense fallback={opsPartnersLazyFallback}>
                <OpsPickupFlow />
              </Suspense>
            </OpsOnly>
          </Protected>
        }
      />
      <Route path="/finance/wallet" element={<Protected><Wallet /></Protected>} />
      <Route path="/finance/transactions" element={<Protected><Transactions /></Protected>} />
      <Route
        path="/finance/billing/cycles"
        element={
          <Protected>
            <Suspense fallback={financeLazyFallback}>
              <BillingCycles />
            </Suspense>
          </Protected>
        }
      />
      <Route
        path="/finance/invoices"
        element={
          <Protected>
            <Suspense fallback={financeLazyFallback}>
              <PartnerInvoices />
            </Suspense>
          </Protected>
        }
      />
      <Route
        path="/finance/credit-notes"
        element={
          <Protected>
            <Suspense fallback={financeLazyFallback}>
              <CreditNotes />
            </Suspense>
          </Protected>
        }
      />
      <Route
        path="/finance/disputes"
        element={
          <Protected>
            <Suspense fallback={financeLazyFallback}>
              <Disputes />
            </Suspense>
          </Protected>
        }
      />
      <Route path="/analytics/dashboard" element={<Protected><DashboardMetrics /></Protected>} />
      <Route path="/analytics/slo-report" element={<Protected><SLOReport /></Protected>} />

      <Route
        path="/lifecycle/metrics"
        element={
          <Protected>
            <Suspense fallback={lifecycleLazyFallback}>
              <LifecycleMetrics />
            </Suspense>
          </Protected>
        }
      />
      <Route
        path="/lifecycle/ranking"
        element={
          <Protected>
            <Suspense fallback={lifecycleLazyFallback}>
              <LifecycleRanking />
            </Suspense>
          </Protected>
        }
      />
      <Route
        path="/lifecycle/health"
        element={
          <Protected>
            <Suspense fallback={lifecycleLazyFallback}>
              <LifecycleHealth />
            </Suspense>
          </Protected>
        }
      />

      <Route
        path="/runtime/slots"
        element={
          <Protected>
            <Suspense fallback={runtimeLazyFallback}>
              <RuntimeDashboard />
            </Suspense>
          </Protected>
        }
      />
      <Route
        path="/runtime/allocations"
        element={
          <Protected>
            <Suspense fallback={runtimeLazyFallback}>
              <RuntimeAllocations />
            </Suspense>
          </Protected>
        }
      />

      <Route path="/ops/lockers" element={<Protected><Lockers /></Protected>} />
      <Route
        path="/ops/lockers/create"
        element={
          <Protected>
            <OpsOnly>
              <OpsLockerCreate />
            </OpsOnly>
          </Protected>
        }
      />
      <Route path="/ops/manifests" element={<Protected><Manifests /></Protected>} />
      <Route
        path="/ops/partners/admin"
        element={
          <Protected>
            <OpsOnly>
              <OpsPartnersAdmin />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/access/user-roles"
        element={
          <Protected>
            <OpsOnly>
              <OpsUserRoles />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/tenants/admin"
        element={
          <Protected>
            <OpsOnly>
              <OpsTenantsAdmin />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/payment-gateway/admin"
        element={
          <Protected>
            <OpsOnly>
              <OpsPaymentGatewayAdmin />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/order-pickup/admin"
        element={
          <Protected>
            <OpsOnly>
              <OpsOrderPickupAdmin />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/marketplace/admin"
        element={
          <Protected>
            <OpsOnly>
              <OpsMarketplaceAdmin />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/finance/admin"
        element={
          <Protected>
            <OpsOnly>
              <OpsFinanceAdmin />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/privacy-compliance/admin"
        element={
          <Protected>
            <OpsOnly>
              <OpsPrivacyComplianceAdmin />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/rentals/admin"
        element={
          <Protected>
            <OpsOnly>
              <OpsRentalAdmin />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/ml/admin"
        element={
          <Protected>
            <OpsOnly>
              <OpsMlAdmin />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/products/admin"
        element={
          <Protected>
            <OpsOnly>
              <OpsProductsAdmin />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/products/assets"
        element={
          <Protected>
            <OpsOnly>
              <OpsProductAssets />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/products/catalog"
        element={
          <Protected>
            <OpsOnly>
              <OpsProductsCatalog />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/products/categories"
        element={
          <Protected>
            <OpsOnly>
              <OpsProductCategories />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/marketing/promotions"
        element={
          <Protected>
            <OpsOnly>
              <OpsPromotionsAdmin />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/products/pricing-fiscal"
        element={
          <Protected>
            <OpsOnly>
              <Navigate to="/ops/products/admin?tab=fiscal" replace />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/products/pricing-rules"
        element={
          <Protected>
            <OpsOnly>
              <Navigate to="/ops/products/admin" replace />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/ops/products/bundles"
        element={
          <Protected>
            <OpsOnly>
              <Navigate to="/ops/products/admin?tab=bundles" replace />
            </OpsOnly>
          </Protected>
        }
      />

      <Route
        path="/intelligence/*"
        element={
          <Protected>
            <IntelligenceOutlet />
          </Protected>
        }
      >
        <Route path="compatibility" element={<Compatibility />} />
        <Route path="predictive-health" element={<PredictiveHealth />} />
        <Route path="occupancy-forecast" element={<OccupancyForecast />} />
        <Route path="feedback-insights" element={<FeedbackInsights />} />
      </Route>

      <Route path="/fiscal/reconcile" element={<Protected><Reconcile /></Protected>} />
      <Route path="/finance/reconcile" element={<Protected><Reconcile /></Protected>} />
      <Route path="/settings/profile" element={<Protected><Profile /></Protected>} />

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

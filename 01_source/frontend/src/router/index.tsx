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
import { FieldChecklist } from '../pages/field/Checklist'
import { NOCDashboard } from '../pages/noc/Dashboard'
import { OrderLookup } from '../pages/support/OrderLookup'
import MvpAccessPage from '../pages/mvp/Access'
import CeoDashboard from '../pages/executive/CeoDashboard'
import { COOLayout } from '../pages/coo/COOLayout'
import { COODashboard } from '../pages/coo/Dashboard'
import {
  ActiveManifests,
  ComplianceReports,
  ExpansionRequests,
  FleetEfficiency,
  InventoryByDepot,
  MTTR,
  NetworkUptime,
  PenaltiesApplied,
  PendingApprovals,
  PickupHealth,
  RealtimeRouting,
  SLAAjustments,
  SupplierSLA,
  UrgentDeadlines,
} from '../pages/coo/CooSubpages'

function DashboardRedirect() {
  const { profile } = useAuth()
  if (profile === 'ceo') return <Navigate to="/dashboard/ceo" replace />
  if (profile === 'coo') return <Navigate to="/coo/dashboard" replace />
  return <Navigate to="/dashboard/admin" replace />
}

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
  if (profile !== 'admin' && profile !== 'ops' && profile !== 'ceo') {
    return <AccessDenied />
  }
  return children
}

function CeoOnly({ children }: { children: JSX.Element }) {
  const { profile } = useAuth()
  if (profile !== 'ceo') {
    return <AccessDenied />
  }
  return children
}

/** Portal COO: apenas perfil `coo` (MVP). CEO/admin não entram pelo UI — usem login COO para testar. */
function CooPortalGate({ children }: { children: JSX.Element }) {
  const { profile } = useAuth()
  if (profile !== 'coo') {
    return <AccessDenied />
  }
  return children
}

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/mvp/access" element={<MvpAccessPage />} />
      <Route path="/legal/privacy" element={<PrivacyPolicy />} />
      <Route path="/legal/terms" element={<TermsOfUse />} />
      <Route path="/support" element={<SupportCenter />} />
      <Route
        path="/support/order/:id"
        element={
          <OrderLookup />
        }
      />
      <Route path="/login" element={<Login />} />

      <Route path="/dashboard" element={<DashboardRedirect />} />
      <Route path="/dashboard/admin" element={<Protected><Dashboard /></Protected>} />
      <Route
        path="/dashboard/ceo"
        element={
          <Protected>
            <CeoOnly>
              <CeoDashboard />
            </CeoOnly>
          </Protected>
        }
      />
      <Route path="/dashboard/partner" element={<Protected><Catalog /></Protected>} />
      <Route path="/dashboard/ops" element={<Protected><Lockers /></Protected>} />

      <Route
        path="/coo"
        element={
          <Protected>
            <CooPortalGate>
              <COOLayout />
            </CooPortalGate>
          </Protected>
        }
      >
        <Route index element={<COODashboard />} />
        <Route path="dashboard" element={<COODashboard />} />
        <Route path="health/pickups" element={<PickupHealth />} />
        <Route path="deadlines/urgent" element={<UrgentDeadlines />} />
        <Route path="logistics/manifests" element={<ActiveManifests />} />
        <Route path="logistics/routing" element={<RealtimeRouting />} />
        <Route path="logistics/inventory" element={<InventoryByDepot />} />
        <Route path="suppliers/sla" element={<SupplierSLA />} />
        <Route path="suppliers/penalties" element={<PenaltiesApplied />} />
        <Route path="suppliers/compliance" element={<ComplianceReports />} />
        <Route path="kpis/uptime" element={<NetworkUptime />} />
        <Route path="kpis/mttr" element={<MTTR />} />
        <Route path="kpis/fleet" element={<FleetEfficiency />} />
        <Route path="approvals/pending" element={<PendingApprovals />} />
        <Route path="approvals/sla" element={<SLAAjustments />} />
        <Route path="approvals/expansion" element={<ExpansionRequests />} />
      </Route>
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
      <Route path="/ops/manifests" element={<Protected><Manifests /></Protected>} />
      <Route
        path="/field/checklist"
        element={
          <Protected>
            <OpsOnly>
              <FieldChecklist />
            </OpsOnly>
          </Protected>
        }
      />
      <Route
        path="/noc/dashboard"
        element={
          <Protected>
            <OpsOnly>
              <NOCDashboard />
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

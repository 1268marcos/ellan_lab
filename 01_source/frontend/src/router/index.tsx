import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import PrivateRoute from '../PrivateRoute'
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
import Reconcile from '../pages/fiscal/Reconcile'
import Profile from '../pages/settings/Profile'
import NotFound from '../pages/NotFound'

const BillingCycles = lazy(() => import('../pages/finance/BillingCycles'))
const PartnerInvoices = lazy(() => import('../pages/finance/PartnerInvoices'))
const CreditNotes = lazy(() => import('../pages/finance/CreditNotes'))
const Disputes = lazy(() => import('../pages/finance/Disputes'))

const financeLazyFallback = (
  <div className="p-6 text-center text-sm text-slate-400">Carregando...</div>
)

function Protected({ children }: { children: JSX.Element }) {
  return (
    <PrivateRoute>
      {children}
    </PrivateRoute>
  )
}

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />

      <Route path="/dashboard" element={<Navigate to="/dashboard/admin" replace />} />
      <Route path="/dashboard/admin" element={<Protected><Dashboard /></Protected>} />
      <Route path="/dashboard/partner" element={<Protected><Catalog /></Protected>} />
      <Route path="/dashboard/ops" element={<Protected><Lockers /></Protected>} />
      <Route path="/partners/catalog" element={<Protected><Catalog /></Protected>} />
      <Route path="/partners/webhooks" element={<Protected><Webhooks /></Protected>} />
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

      <Route path="/ops/lockers" element={<Protected><Lockers /></Protected>} />
      <Route path="/ops/manifests" element={<Protected><Manifests /></Protected>} />
      <Route path="/intelligence/compatibility" element={<Protected><Compatibility /></Protected>} />
      <Route path="/fiscal/reconcile" element={<Protected><Reconcile /></Protected>} />
      <Route path="/finance/reconcile" element={<Protected><Reconcile /></Protected>} />
      <Route path="/settings/profile" element={<Protected><Profile /></Protected>} />

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

import { Navigate, Route, Routes } from 'react-router-dom'
import PrivateRoute from '../PrivateRoute'
import MainLayout from '../layouts/MainLayout'
import Dashboard from '../pages/Dashboard'
import Login from '../pages/Login'
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

function Protected({ children }: { children: React.ReactNode }) {
  return (
    <PrivateRoute>
      <MainLayout>{children}</MainLayout>
    </PrivateRoute>
  )
}

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
      <Route path="/partners/catalog" element={<Protected><Catalog /></Protected>} />
      <Route path="/partners/webhooks" element={<Protected><Webhooks /></Protected>} />
      <Route path="/finance/wallet" element={<Protected><Wallet /></Protected>} />
      <Route path="/finance/transactions" element={<Protected><Transactions /></Protected>} />
      <Route path="/analytics/dashboard" element={<Protected><DashboardMetrics /></Protected>} />
      <Route path="/analytics/slo-report" element={<Protected><SLOReport /></Protected>} />

      <Route path="/ops/lockers" element={<Protected><Lockers /></Protected>} />
      <Route path="/ops/manifests" element={<Protected><Manifests /></Protected>} />
      <Route path="/intelligence/compatibility" element={<Protected><Compatibility /></Protected>} />
      <Route path="/fiscal/reconcile" element={<Protected><Reconcile /></Protected>} />
      <Route path="/finance/reconcile" element={<Protected><Reconcile /></Protected>} />
      <Route path="/settings/profile" element={<Protected><Profile /></Protected>} />

      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}


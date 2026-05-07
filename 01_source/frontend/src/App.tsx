import { BrowserRouter, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './AuthContext'
import AppRouter from './router'
import MainLayout from './layouts/MainLayout'
import ExecutiveLayout from './layouts/ExecutiveLayout'

function AppContent() {
  const location = useLocation()
  const { isAuthenticated, profile } = useAuth()

  if (location.pathname === '/login') {
    return <AppRouter />
  }

  if (isAuthenticated && profile === 'ceo') {
    return (
      <ExecutiveLayout>
        <AppRouter />
      </ExecutiveLayout>
    )
  }

  return (
    <MainLayout>
      <AppRouter />
    </MainLayout>
  )
}

export default function App() {
  return (
    <BrowserRouter basename="/v1">
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  )
}

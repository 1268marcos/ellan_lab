import { BrowserRouter, useLocation } from 'react-router-dom'
import { AuthProvider } from './AuthContext'
import AppRouter from './router'
import MainLayout from './layouts/MainLayout'

function AppContent() {
  const location = useLocation()
  if (location.pathname === '/login') {
    return <AppRouter />
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

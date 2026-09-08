// GeoForraje Frontend - App Principal
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { LoginPage } from '@/modules/auth/pages/LoginPage'
import { RegisterPage } from '@/modules/auth/pages/RegisterPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { LotsPage } from '@/modules/lots/pages/LotsPage'
import { LotDetailPage } from '@/modules/lots/pages/LotDetailPage'
import { LotFormPage } from '@/modules/lots/pages/LotFormPage'
import { useAuthStore } from '@/modules/auth/store/authStore'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, hydrate } = useAuthStore()
  
  // Hidratar store al montar
  React.useEffect(() => {
    hydrate()
  }, [hydrate])

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, hydrate } = useAuthStore()
  
  React.useEffect(() => {
    hydrate()
  }, [hydrate])

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }
  
  return <>{children}</>
}

export function App() {
  return (
    <Routes>
      {/* Rutas públicas */}
      <Route path="/login" element={
        <PublicRoute>
          <LoginPage />
        </PublicRoute>
      } />
      <Route path="/register" element={
        <PublicRoute>
          <RegisterPage />
        </PublicRoute>
      } />
      
      {/* Rutas protegidas */}
      <Route element={
        <PrivateRoute>
          <Layout />
        </PrivateRoute>
      }>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/lots" element={<LotsPage />} />
        <Route path="/lots/new" element={<LotFormPage />} />
        <Route path="/lots/:id" element={<LotDetailPage />} />
        <Route path="/lots/:id/edit" element={<LotFormPage />} />
      </Route>
      
      {/* Redirect root */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
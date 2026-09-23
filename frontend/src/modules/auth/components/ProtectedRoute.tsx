// ProtectedRoute.tsx - Wrapper para rutas protegidas
import { Navigate, useLocation } from "react-router-dom"
import { useAuth } from "@/modules/auth/hooks/useAuth"

export const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  // Mientras se carga, mostramos nada (o un spinner)
  if (isLoading) {
    return null
  }

  // Si no está autenticado, redirigir al login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  // Si está autenticado, renderizar los children
  return children
}
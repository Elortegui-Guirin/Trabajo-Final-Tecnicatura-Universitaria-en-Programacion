// DashboardPage.tsx - Página protegida de ejemplo
import { useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "@/modules/auth/hooks/useAuth"

export const DashboardPage = () => {
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuth()

  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login")
    }
  }, [isAuthenticated, navigate])

  const handleLogout = () => {
    logout()
    navigate("/login")
  }

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6">Panel de Control</h2>
      
      {user ? (
        <div className="mb-4">
          <p className="font-medium">Bienvenido, {user.full_name || user.email}</p>
        </div>
      ) : (
        <p>Cargando usuario...</p>
      )}

      <button
        onClick={handleLogout}
        className="mt-4 py-2 rounded bg-red-600 text-white"
      >
        Cerrar sesión
      </button>
    </div>
  )
}
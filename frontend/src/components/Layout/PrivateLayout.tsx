// PrivateLayout.tsx - Layout con outlet protegido
import { Outlet } from "react-router-dom"
import { ProtectedRoute } from "@/modules/auth/components/ProtectedRoute"

export const PrivateLayout = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <h1 className="text-xl font-semibold">GeoForraje 1.0</h1>
        </div>
      </header>

      <main className="py-6">
        <ProtectedRoute>
          <Outlet />
        </ProtectedRoute>
      </main>
    </div>
  )
}
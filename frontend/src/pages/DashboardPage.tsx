// GeoForraje Frontend - Dashboard Page (placeholder)
export function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Bienvenido a GeoForraje 1.0</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-2">Próximos pasos</h3>
          <ul className="space-y-2 text-gray-600 text-sm">
            <li>• FASE 2: Autenticación y usuarios</li>
            <li>• FASE 3: CRUD de lotes</li>
            <li>• FASE 4: Mapa interactivo Leaflet</li>
            <li>• FASE 5: Análisis raster y despliegue</li>
          </ul>
        </div>

        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-2">Estado del sistema</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">API Backend</span>
              <span className="text-green-600 font-medium">Operativo</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Base de Datos</span>
              <span className="text-green-600 font-medium">Conectada</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">PostGIS</span>
              <span className="text-green-600 font-medium">Habilitado</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-2">Accesos rápidos</h3>
          <div className="space-y-2">
            <a href="/lots/new" className="btn-primary w-full text-center">Crear primer lote</a>
            <a href="/lots" className="btn-secondary w-full text-center">Ver mis lotes</a>
          </div>
        </div>
      </div>
    </div>
  )
}
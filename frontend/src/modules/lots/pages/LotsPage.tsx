// Lots Page - Placeholder FASE 3
import { Link } from 'react-router-dom'

export function LotsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mis Lotes</h1>
          <p className="text-gray-600 mt-1">Gestiona tus parcelas georreferenciadas</p>
        </div>
        <Link to="/lots/new" className="btn-primary">
          <span className="mr-2">+</span> Nuevo Lote
        </Link>
      </div>

      <div className="card">
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🌾</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No hay lotes aún</h3>
          <p className="text-gray-600 mb-6">Crea tu primer lote para empezar a analizar tus parcelas</p>
          <Link to="/lots/new" className="btn-primary inline-flex">
            Crear primer lote
          </Link>
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Próximas funcionalidades (FASE 3)</h3>
        <ul className="space-y-2 text-gray-600 text-sm">
          <li>• Listado paginado con búsqueda y filtros</li>
          <li>• Crear lote con mapa interactivo (dibujar polígono)</li>
          <li>• Editar geometría y nombre del lote</li>
          <li>• Ver detalle con mapa de solo lectura</li>
          <li>• Eliminar lote con confirmación</li>
          <li>• Cálculo automático de área en hectáreas</li>
        </ul>
      </div>
    </div>
  )
}
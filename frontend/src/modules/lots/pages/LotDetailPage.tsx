// Lot Detail Page - Placeholder FASE 3
import { useParams, Link } from 'react-router-dom'

export function LotDetailPage() {
  const { id } = useParams()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Detalle del Lote</h1>
          <p className="text-gray-600 mt-1">ID: {id}</p>
        </div>
        <div className="flex gap-2">
          <Link to={`/lots/${id}/edit`} className="btn-secondary">Editar</Link>
          <Link to="/lots" className="btn-secondary">Volver</Link>
        </div>
      </div>

      <div className="card">
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🗺️</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Mapa del lote (FASE 4)</h3>
          <p className="text-gray-600 mb-6">Aquí se mostrará el mapa Leaflet con el polígono del lote</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="card text-center">
          <div className="text-3xl font-bold text-primary-600">—</div>
          <div className="text-gray-600 text-sm">Área (ha)</div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-bold text-primary-600">—</div>
          <div className="text-gray-600 text-sm">Fecha creación</div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-bold text-primary-600">—</div>
          <div className="text-gray-600 text-sm">Última actualización</div>
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Acciones (FASE 5)</h3>
        <div className="flex gap-2">
          <button className="btn-primary" disabled>Analizar recurso 1</button>
          <button className="btn-secondary" disabled>Analizar recurso 2</button>
          <button className="btn-secondary" disabled>Analizar recurso 3</button>
          <button className="btn-secondary" disabled>Analizar recurso 4</button>
        </div>
        <p className="text-sm text-gray-500 mt-2">Los botones se activarán cuando se implemente el análisis raster</p>
      </div>
    </div>
  )
}
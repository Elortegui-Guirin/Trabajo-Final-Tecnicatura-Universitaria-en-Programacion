// LotDetail.tsx - Vista de detalle de lote con mapa solo lectura
import { MapEditor } from '@/components/MapView/MapEditor'
import { Link } from 'react-router-dom'
import type { LotRead } from '@/types/api'

interface LotDetailProps {
  lot: LotRead
  onAnalyze?: (lot: LotRead, resourceType: string) => void
}

export function LotDetail({ lot, onAnalyze }: LotDetailProps) {
  const geojsonFeature = {
    type: 'Feature',
    properties: {},
    geometry: lot.geometry,
  } as const

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{lot.name}</h1>
          <p className="text-gray-600 mt-1">ID: {lot.id}</p>
        </div>
        <div className="flex gap-2">
          <Link to={`/lots/${lot.id}/edit`} className="btn-secondary">Editar</Link>
          <Link to="/lots" className="btn-secondary">Volver</Link>
        </div>
      </div>

      {/* Mapa solo lectura */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Ubicación del lote</h3>
        <MapEditor
          initialGeometry={geojsonFeature}
          onGeometryChange={() => {}}
          readOnly={true}
          height="500px"
        />
      </div>

      {/* Métricas */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="card text-center">
          <div className="text-3xl font-bold text-primary-600">{lot.area_ha.toFixed(2)}</div>
          <div className="text-gray-600 text-sm">Área (ha)</div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-bold text-primary-600">{new Date(lot.created_at).toLocaleDateString('es-AR')}</div>
          <div className="text-gray-600 text-sm">Creado</div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-bold text-primary-600">{new Date(lot.updated_at).toLocaleDateString('es-AR')}</div>
          <div className="text-gray-600 text-sm">Actualizado</div>
        </div>
      </div>

      {/* Acciones de análisis - FASE 5 */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Análisis de recursos (FASE 5)</h3>
        <div className="flex flex-wrap gap-2">
          {['resource_1', 'resource_2', 'resource_3', 'resource_4'].map((resource, i) => (
            <button
              key={resource}
              onClick={() => onAnalyze?.(lot, resource)}
              disabled={true}
              className="btn-secondary"
            >
              Analizar recurso {i + 1}
            </button>
          ))}
        </div>
        <p className="text-sm text-gray-500 mt-2">Disponible en Fase 5 - Análisis Raster</p>
      </div>
    </div>
  )
}
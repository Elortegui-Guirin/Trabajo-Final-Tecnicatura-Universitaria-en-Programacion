// LotDetail.tsx - Vista de detalle de lote con mapa solo lectura
import { MapEditor } from '@/components/MapView/MapEditor'
import { Link } from 'react-router-dom'
import type { LotRead } from '@/types/api'

interface LotDetailProps {
  lot: LotRead
}

export function LotDetail({ lot }: LotDetailProps) {
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

      {/* Acciones de análisis - NUEVO: Link a historial de análisis */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Análisis forrajero</h3>
        <Link 
          to={`/lots/${lot.id}/analyses`}
          className="btn-primary inline-flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Ver historial de análisis
        </Link>
        <p className="text-sm text-gray-500 mt-2">
          Gestiona y visualiza análisis de biomasa, cobertura, índice vegetación y humedad.
        </p>
      </div>
    </div>
  )
}
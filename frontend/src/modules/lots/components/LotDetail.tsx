// LotDetail.tsx - Vista de detalle de lote con mapa solo lectura e historial de versiones
import { useState } from 'react'
import { MapEditor } from '@/components/MapView/MapEditor'
import { Link } from 'react-router-dom'
import { useLotVersions } from '@/modules/lots/hooks/useLots'
import type { LotRead, LotVersionRead } from '@/types/api'

interface LotDetailProps {
  lot: LotRead
}

export function LotDetail({ lot }: LotDetailProps) {
  const [showVersions, setShowVersions] = useState(false)
  const { data: versions, isLoading: versionsLoading } = useLotVersions(lot.id)

  const geojsonFeature = {
    type: 'Feature',
    properties: {},
    geometry: lot.geometry,
  } as const

  const isDeleted = !!lot.deleted_at

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-gray-900">{lot.name}</h1>
            {isDeleted && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                Eliminado
              </span>
            )}
          </div>
          <p className="text-gray-600 mt-1">ID: {lot.id}</p>
        </div>
        <div className="flex gap-2">
          {!isDeleted && (
            <Link to={`/lots/${lot.id}/edit`} className="btn-secondary">Editar</Link>
          )}
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
      <div className="grid gap-4 md:grid-cols-4">
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
        {isDeleted && (
          <div className="card text-center">
            <div className="text-3xl font-bold text-red-600">{new Date(lot.deleted_at!).toLocaleDateString('es-AR')}</div>
            <div className="text-gray-600 text-sm">Eliminado</div>
          </div>
        )}
      </div>

      {/* Historial de versiones */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">Historial de geometrías</h3>
          <button
            onClick={() => setShowVersions(!showVersions)}
            className="btn-secondary text-sm"
          >
            {showVersions ? 'Ocultar' : `Ver historial (${versions?.length || 0})`}
          </button>
        </div>

        {showVersions && (
          <div className="space-y-3">
            {versionsLoading ? (
              <div className="py-8 text-center text-gray-500">Cargando historial...</div>
            ) : versions && versions.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="px-4 py-2 text-left font-medium text-gray-600">Versión</th>
                      <th className="px-4 py-2 text-left font-medium text-gray-600">Fecha</th>
                      <th className="px-4 py-2 text-left font-medium text-gray-600">Área (ha)</th>
                      <th className="px-4 py-2 text-left font-medium text-gray-600">Motivo</th>
                      <th className="px-4 py-2 text-left font-medium text-gray-600">Modificado por</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {versions.map((v: LotVersionRead) => (
                      <tr key={v.id} className="hover:bg-gray-50">
                        <td className="px-4 py-2 font-medium text-gray-900">v{v.version_number}</td>
                        <td className="px-4 py-2 text-gray-600">
                          {new Date(v.created_at).toLocaleString('es-AR')}
                        </td>
                        <td className="px-4 py-2 text-gray-600">{v.area_ha.toFixed(2)}</td>
                        <td className="px-4 py-2 text-gray-600">{v.change_reason || '—'}</td>
                        <td className="px-4 py-2 text-gray-500 text-xs">{v.changed_by.slice(0, 8)}...</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-8 text-center text-gray-500">
                Sin historial de versiones disponible
              </div>
            )}
          </div>
        }
      </div>

      {/* Acciones de análisis */}
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

      {/* Acciones de restauración si está eliminado */}
      {isDeleted && (
        <div className="card border-red-200 bg-red-50">
          <h3 className="font-semibold text-red-800 mb-2">Lote eliminado</h3>
          <p className="text-red-700 mb-4">Este lote fue eliminado el {new Date(lot.deleted_at!).toLocaleDateString('es-AR')}. Los análisis históricos se conservan.</p>
          <button className="btn-secondary text-red-600 border-red-300 hover:bg-red-50">
            Restaurar lote
          </button>
        </div>
      )}
    </div>
  )
}
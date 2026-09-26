// AnalysisDetail - Detalle completo de análisis con métricas y gráfico
import { useMemo } from 'react'
import { MapEditor } from '@/components/MapView/MapEditor'
import { AnalysisChart } from './AnalysisChart'
import type { AnalysisRead, GeoJSONPolygon } from '@/types/analysis'

interface AnalysisDetailProps {
  analysis: AnalysisRead
  lotGeometry?: GeoJSONPolygon
  lotName?: string
}

const metricCards = [
  { key: 'average_rate' as const, label: 'Tasa promedio', color: 'text-primary-600' },
  { key: 'min_value', label: 'Mínimo', color: 'text-blue-600' },
  { key: 'max_value', label: 'Máximo', color: 'text-red-600' },
  { key: 'std_dev', label: 'Desv. estándar', color: 'text-purple-600' },
] as const

export function AnalysisDetail({ analysis, lotGeometry, lotName }: AnalysisDetailProps) {
  const percentiles = useMemo(() => analysis.percentiles || {}, [analysis.percentiles])

  const resourceLabels: Record<string, string> = {
    resource_1: 'Biomasa verde (kg/ha)',
    resource_2: 'Cobertura suelo (%)',
    resource_3: 'Índice vegetación (NDVI)',
    resource_4: 'Humedad suelo (%)',
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Detalle de Análisis</h1>
          <p className="text-gray-600 mt-1">
            Lote: {lotName || analysis.lot_id} • 
            Recurso: {resourceLabels[analysis.resource_type] || analysis.resource_type}
          </p>
        </div>
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
          analysis.status === 'completed' ? 'bg-green-100 text-green-700' :
          analysis.status === 'processing' ? 'bg-blue-100 text-blue-700' :
          analysis.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
          'bg-red-100 text-red-700'
        }`}>
          {analysis.status}
        </span>
      </div>

      {/* Mapa del lote (solo lectura) */}
      {lotGeometry && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Ubicación del lote analizado</h3>
          <MapEditor
            initialGeometry={{ type: 'Feature', properties: {}, geometry: lotGeometry }}
            onGeometryChange={() => {}}
            readOnly={true}
            height="400px"
          />
        </div>
      )}

      {/* Métricas principales */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metricCards.map(({ key, label, color }) => {
          const value = analysis[key]
          return value !== undefined && value !== null ? (
            <div key={key} className="card text-center">
              <div className={`text-3xl font-bold ${color}`}>
                {typeof value === 'number' ? value.toFixed(4) : value}
              </div>
              <div className="text-gray-600 text-sm">{label}</div>
            </div>
          ) : null
        })}
      </div>

      {/* Percentiles */}
      {Object.keys(percentiles).length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Percentiles</h3>
          <div className="grid gap-4 md:grid-cols-5">
            {(['p25', 'p50', 'p75', 'p90', 'p95'] as const).map((p) => (
              <div key={p} className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-gray-900">
                  {percentiles[p] !== undefined ? percentiles[p].toFixed(4) : '—'}
                </div>
                <div className="text-gray-600 text-sm">{p.toUpperCase()}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Gráfico de serie temporal (si hay datos) */}
      <AnalysisChart 
        analysisId={analysis.id} 
        resourceType={analysis.resource_type}
        lotName={lotName}
      />

      {/* Info técnica */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Información técnica</h3>
        <dl className="grid gap-2 md:grid-cols-2 text-sm">
          <dt className="text-gray-600">ID Análisis</dt>
          <dd className="font-mono text-gray-900">{analysis.id}</dd>
          <dt className="text-gray-600">Fecha análisis</dt>
          <dd>{new Date(analysis.analyzed_at).toLocaleString('es-AR')}</dd>
          <dt className="text-gray-600">Raster origen</dt>
          <dd className="font-mono text-gray-900 truncate">{analysis.raster_file_reference}</dd>
          <dt className="text-gray-600">Estado</dt>
          <dd>{analysis.status}</dd>
          {analysis.error_message && (
            <>
              <dt className="text-gray-600">Error</dt>
              <dd className="text-red-600">{analysis.error_message}</dd>
            </>
          )}
        </dl>
      </div>
    </div>
  )
}
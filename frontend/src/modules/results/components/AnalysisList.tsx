// AnalysisList - Historial de análisis con tabla
import { useState } from 'react'
import { useAnalyses } from '@/modules/results/hooks/useAnalyses'
import type { AnalysisRead, ResourceType } from '@/types/analysis'

interface AnalysisListProps {
  lotId?: string
  onView?: (analysis: AnalysisRead) => void
}

const resourceLabels: Record<ResourceType, { label: string; color: string }> = {
  resource_1: { label: 'Biomasa verde', color: 'bg-green-100 text-green-700' },
  resource_2: { label: 'Cobertura suelo', color: 'bg-blue-100 text-blue-700' },
  resource_3: { label: 'Índice vegetación', color: 'bg-emerald-100 text-emerald-700' },
  resource_4: { label: 'Humedad suelo', color: 'bg-cyan-100 text-cyan-700' },
}

const statusConfig = {
  pending: { label: 'Pendiente', color: 'bg-yellow-100 text-yellow-700' },
  processing: { label: 'Procesando', color: 'bg-blue-100 text-blue-700' },
  completed: { label: 'Completado', color: 'bg-green-100 text-green-700' },
  failed: { label: 'Error', color: 'bg-red-100 text-red-700' },
} as const

export function AnalysisList({ lotId, onView }: AnalysisListProps) {
  const [page, setPage] = useState(1)
  const [resourceFilter, setResourceFilter] = useState<ResourceType | ''>('')
  const size = 10

  const { data, isLoading, error, refetch } = useAnalyses({ 
    lot_id: lotId, 
    resource_type: resourceFilter || undefined,
    page,
    size,
  })

  const analyses = data?.items || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / size)

  if (isLoading && !data) return <div className="py-8 text-center text-gray-500">Cargando análisis...</div>
  if (error) return <div className="py-8 text-center text-red-500">Error al cargar análisis</div>

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2">
          <select
            value={resourceFilter}
            onChange={(e) => { setResourceFilter(e.target.value as ResourceType | ''); setPage(1) }}
            className="input py-2 px-3 text-sm max-w-xs"
          >
            <option value="">Todos los recursos</option>
            <option value="resource_1">Biomasa verde</option>
            <option value="resource_2">Cobertura suelo</option>
            <option value="resource_3">Índice vegetación</option>
            <option value="resource_4">Humedad suelo</option>
          </select>
        </div>
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-4 py-3 text-left font-medium text-gray-600">Fecha</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Recurso</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Tasa promedio</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Estado</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {analyses.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-gray-500">
                  No hay análisis. <button className="text-primary-600 hover:underline">Crea uno desde el lote</button>
                </td>
              </tr>
            ) : (
              analyses.map((analysis) => (
                <tr key={analysis.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-600">
                    {new Date(analysis.analyzed_at).toLocaleDateString('es-AR', { 
                      day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' 
                    })}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${resourceLabels[analysis.resource_type].color}`}>
                      {resourceLabels[analysis.resource_type].label}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {analysis.average_rate.toFixed(4)}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusConfig[analysis.status].color}`}>
                      {statusConfig[analysis.status].label}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {onView && analysis.status === 'completed' && (
                      <button
                        onClick={() => onView(analysis)}
                        className="p-2 text-primary-600 hover:bg-primary-50 rounded-lg transition"
                        title="Ver detalle"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      </button>
                    )}
                    {analysis.status === 'failed' && (
                      <span className="text-red-500 text-sm" title={analysis.error_message || 'Error desconocido'}>
                        ⚠
                      </span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Mostrando {((page - 1) * size) + 1} a {Math.min(page * size, total)} de {total}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn-secondary text-sm"
            >
              Anterior
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="btn-secondary text-sm"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
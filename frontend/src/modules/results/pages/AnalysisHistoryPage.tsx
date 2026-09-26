// AnalysisHistoryPage - Historial de análisis de un lote
import { useParams } from 'react-router-dom'
import { useLot } from '@/modules/lots/hooks/useLots'
import { AnalysisList } from '@/modules/results/components/AnalysisList'
import { useCreateAnalysis } from '@/modules/results/hooks/useAnalyses'
import type { ResourceType } from '@/types/analysis'

export function AnalysisHistoryPage() {
  const { id } = useParams<{ id: string }>()
  const { data: lot, isLoading: lotLoading } = useLot(id || '')
  const createMutation = useCreateAnalysis()

  const handleAnalyze = async (resourceType: ResourceType) => {
    try {
      await createMutation.mutateAsync({ lot_id: id!, resource_type: resourceType })
    } catch (err) {
      console.error('Error iniciando análisis:', err)
    }
  }

  if (lotLoading) return <div className="py-8 text-center text-gray-500">Cargando lote...</div>
  if (!lot) return <div className="py-8 text-center text-red-500">Lote no encontrado</div>

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Análisis de {lot.name}</h1>
          <p className="text-gray-600 mt-1">Área: {lot.area_ha.toFixed(2)} ha</p>
        </div>
      </div>

      {/* Botones de análisis rápido */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Nuevo análisis</h3>
        <div className="flex flex-wrap gap-2">
          {(['resource_1', 'resource_2', 'resource_3', 'resource_4'] as ResourceType[]).map((rt, i) => (
            <button
              key={rt}
              onClick={() => handleAnalyze(rt)}
              disabled={createMutation.isPending}
              className="btn-secondary"
            >
              Analizar recurso {i + 1}
              {createMutation.isPending && '...'}
            </button>
          ))}
        </div>
        <p className="text-sm text-gray-500 mt-2">
          El análisis se ejecuta en segundo plano. La tabla se actualizará automáticamente al completarse.
        </p>
      </div>

      {/* Lista de análisis */}
      <div className="card">
        <AnalysisList lotId={id} />
      </div>
    </div>
  )
}
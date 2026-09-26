// AnalysisDetailPage - Detalle completo de un análisis
import { useParams } from 'react-router-dom'
import { useAnalysis } from '@/modules/results/hooks/useAnalyses'
import { useLot } from '@/modules/lots/hooks/useLots'
import { AnalysisDetail } from '@/modules/results/components/AnalysisDetail'

export function AnalysisDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: analysis, isLoading, error } = useAnalysis(id || '')
  
  // Cargar lote para geometría y nombre
  const lotId = analysis?.lot_id
  const { data: lot } = useLot(lotId || '')

  if (isLoading) return <div className="py-8 text-center text-gray-500">Cargando análisis...</div>
  if (error || !analysis) return <div className="py-8 text-center text-red-500">Análisis no encontrado</div>

  return (
    <AnalysisDetail 
      analysis={analysis} 
      lotGeometry={lot?.geometry} 
      lotName={lot?.name} 
    />
  )
}
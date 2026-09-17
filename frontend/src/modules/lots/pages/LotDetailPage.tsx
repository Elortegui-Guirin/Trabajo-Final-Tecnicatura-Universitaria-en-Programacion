// LotDetailPage.tsx - Detalle de lote
import { useParams } from 'react-router-dom'
import { useLot } from '@/modules/lots/hooks/useLots'
import { LotDetail } from '@/modules/lots/components/LotDetail'

export function LotDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: lot, isLoading, error } = useLot(id || '')

  if (isLoading) return <div className="py-8 text-center text-gray-500">Cargando lote...</div>
  if (error || !lot) return <div className="py-8 text-center text-red-500">Lote no encontrado</div>

  return <LotDetail lot={lot} />
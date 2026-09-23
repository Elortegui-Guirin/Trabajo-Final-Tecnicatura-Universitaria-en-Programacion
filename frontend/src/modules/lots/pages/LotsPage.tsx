// LotsPage.tsx - Listado de lotes
import { LotList } from '@/modules/lots/components/LotList'
import { useNavigate } from 'react-router-dom'
import { useLot } from '@/modules/lots/hooks/useLots'

export function LotsPage() {
  const navigate = useNavigate()

  const handleView = (lot: any) => {
    navigate(`/lots/${lot.id}`)
  }

  const handleEdit = (lot: any) => {
    navigate(`/lots/${lot.id}/edit`)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Mis Lotes</h1>
        <p className="text-gray-600 mt-1">Gestiona tus parcelas georreferenciadas</p>
      </div>

      <div className="card">
        <LotList onView={handleView} onEdit={handleEdit} />
      </div>
    </div>
  )
}
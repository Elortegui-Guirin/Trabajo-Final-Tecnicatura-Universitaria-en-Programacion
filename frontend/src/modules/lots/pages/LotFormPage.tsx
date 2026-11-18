// LotFormPage.tsx - Crear/editar lote
import { useParams } from 'react-router-dom'
import { LotForm } from '@/modules/lots/components/LotForm'

export function LotFormPage() {
  const { id } = useParams<{ id: string }>()
  const isEdit = !!id
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{isEdit ? 'Editar lote' : 'Nuevo Lote'}</h1>
        <p className="text-gray-600 mt-1">{isEdit ? 'Cambiá el nombre o redibujá el polígono. Cada cambio de geometría queda en el historial de versiones.' : 'Dibuja un polígono en el mapa para definir el lote'}</p>
      </div>

      <div className="card">
        <LotForm />
      </div>
    </div>
  )
}
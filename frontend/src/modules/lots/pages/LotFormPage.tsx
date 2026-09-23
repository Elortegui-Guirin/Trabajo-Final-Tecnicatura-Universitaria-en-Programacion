// LotFormPage.tsx - Crear/editar lote
import { LotForm } from '@/modules/lots/components/LotForm'

export function LotFormPage() {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Nuevo Lote</h1>
        <p className="text-gray-600 mt-1">Dibuja un polígono en el mapa para definir el lote</p>
      </div>

      <div className="card">
        <LotForm />
      </div>
    </div>
  )
}
// Lot Form Page - Placeholder FASE 3/4
import { useParams, useNavigate } from 'react-router-dom'

export function LotFormPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = !!id

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{isEdit ? 'Editar' : 'Crear'} Lote</h1>
          <p className="text-gray-600 mt-1">{isEdit ? `Editando lote: ${id}` : 'Dibuja un polígono en el mapa para definir el lote'}</p>
        </div>
        <button onClick={() => navigate('/lots')} className="btn-secondary">Cancelar</button>
      </div>

      <div className="card">
        <form className="space-y-6">
          <div>
            <label htmlFor="name" className="label">Nombre del lote</label>
            <input
              id="name"
              type="text"
              className="input"
              placeholder="Ej: Lote Norte, Potrero 1, Campo Principal"
              defaultValue={isEdit ? 'Lote de ejemplo' : ''}
            />
          </div>

          <div>
            <label className="label">Geometría (FASE 4)</label>
            <div className="aspect-video bg-gray-100 rounded-lg border border-gray-200 flex items-center justify-center">
              <div className="text-center text-gray-500">
                <div className="text-4xl mb-2">🗺️</div>
                <p>Mapa interactivo Leaflet</p>
                <p className="text-sm">Toolbar: dibujar, editar, eliminar polígono</p>
                <p className="text-sm">GeoJSON capturado automáticamente</p>
              </div>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="label">Área calculada (ha)</label>
              <input type="text" className="input bg-gray-50" value="—" readOnly />
            </div>
            <div>
              <label className="label">SRID</label>
              <input type="text" className="input bg-gray-50" value="EPSG:4326 (WGS84)" readOnly />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={() => navigate('/lots')} className="btn-secondary">Cancelar</button>
            <button type="submit" className="btn-primary">{isEdit ? 'Actualizar' : 'Crear lote'}</button>
          </div>
        </form>
      </div>

      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Funcionalidades por fase</h3>
        <ul className="space-y-1 text-sm text-gray-600">
          <li className="flex items-center gap-2"><span className="text-green-500">✓</span> FASE 3: Formulario básico + validación nombre</li>
          <li className="flex items-center gap-2"><span className="text-blue-500">→</span> FASE 4: Mapa Leaflet + leaflet.pm (dibujar/editar polígono)</li>
          <li className="flex items-center gap-2"><span className="text-blue-500">→</span> FASE 4: Captura GeoJSON + cálculo área client-side</li>
          <li className="flex items-center gap-2"><span className="text-blue-500">→</span> FASE 3: Validación server-side geometría (Shapely + PostGIS)</li>
        </ul>
      </div>
    </div>
  )
}
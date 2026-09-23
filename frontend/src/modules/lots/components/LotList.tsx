// LotList.tsx - Tabla de lotes con paginación y búsqueda
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useLots, useDeleteLot } from '@/modules/lots/hooks/useLots'
import type { LotRead } from '@/types/api'

interface LotListProps {
  onView?: (lot: LotRead) => void
  onEdit?: (lot: LotRead) => void
}

export function LotList({ onView, onEdit }: LotListProps) {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const size = 10

  const { data, isLoading, error, refetch } = useLots({ page, size, search })
  const deleteMutation = useDeleteLot()

  const handleDelete = async (id: string) => {
    if (!window.confirm('¿Eliminar este lote? Se borrarán también sus análisis.')) return
    try {
      await deleteMutation.mutateAsync(id)
      refetch()
    } catch (err) {
      alert('Error al eliminar lote')
    }
  }

  if (isLoading && !data) return <div className="py-8 text-center text-gray-500">Cargando lotes...</div>
  if (error) return <div className="py-8 text-center text-red-500">Error al cargar lotes</div>

  const lots = data?.items || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / size)

  return (
    <div className="space-y-4">
      {/* Búsqueda y acciones */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="relative max-w-md w-full">
          <input
            type="text"
            placeholder="Buscar por nombre..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <Link to="/lots/new" className="btn-primary whitespace-nowrap">
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Nuevo Lote
        </Link>
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-4 py-3 text-left font-medium text-gray-600">Nombre</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Área (ha)</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Creado</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Actualizado</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {lots.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-gray-500">
                  No hay lotes. <Link to="/lots/new" className="text-primary-600 hover:underline">Crea el primero</Link>
                </td>
              </tr>
            ) : (
              lots.map((lot) => (
                <tr key={lot.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{lot.name}</td>
                  <td className="px-4 py-3 text-gray-600">{lot.area_ha.toFixed(2)}</td>
                  <td className="px-4 py-3 text-gray-500">{new Date(lot.created_at).toLocaleDateString('es-AR')}</td>
                  <td className="px-4 py-3 text-gray-500">{new Date(lot.updated_at).toLocaleDateString('es-AR')}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {onView && (
                        <button
                          onClick={() => onView(lot)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition"
                          title="Ver detalle"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        </button>
                      )}
                      {onEdit && (
                        <Link
                          to={`/lots/${lot.id}/edit`}
                          className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition"
                          title="Editar"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </Link>
                      )}
                      <button
                        onClick={() => handleDelete(lot.id)}
                        disabled={deleteMutation.isPending}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition disabled:opacity-50"
                        title="Eliminar"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
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
// LotList.tsx - Tabla de lotes con paginación, búsqueda y filtros avanzados
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useLots, useDeleteLot, useRestoreLot } from '@/modules/lots/hooks/useLots'
import type { LotRead, LotSearchParams } from '@/types/api'

interface LotListProps {
  onView?: (lot: LotRead) => void
  onEdit?: (lot: LotRead) => void
}

export function LotList({ onView, onEdit }: LotListProps) {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [areaMin, setAreaMin] = useState('')
  const [areaMax, setAreaMax] = useState('')
  const [bbox, setBbox] = useState('')
  const size = 10

  // Construir params para useLots
  const searchParams: LotSearchParams = {
    search: search || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    area_min: areaMin ? parseFloat(areaMin) : undefined,
    area_max: areaMax ? parseFloat(areaMax) : undefined,
    bbox: bbox || undefined,
  }

  const { data, isLoading, error, refetch } = useLots({ page, size, ...searchParams })
  const deleteMutation = useDeleteLot()
  const restoreMutation = useRestoreLot()

  const handleDelete = async (id: string) => {
    if (!window.confirm('¿Eliminar este lote? (Soft delete - se conservan análisis históricos)')) return
    try {
      await deleteMutation.mutateAsync(id)
      refetch()
    } catch (err) {
      alert('Error al eliminar lote')
    }
  }

  const handleRestore = async (id: string) => {
    try {
      await restoreMutation.mutateAsync(id)
      refetch()
    } catch (err) {
      alert('Error al restaurar lote')
    }
  }

  const handleSearchChange = (newSearch: string) => {
    setSearch(newSearch)
    setPage(1)
  }

  const handleFilterChange = () => {
    setPage(1)
  }

  if (isLoading && !data) return <div className="py-8 text-center text-gray-500">Cargando lotes...</div>
  if (error) return <div className="py-8 text-center text-red-500">Error al cargar lotes</div>

  const lots = data?.items || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / size)

  return (
    <div className="space-y-4">
      {/* Búsqueda y filtros */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="relative max-w-md w-full">
            <input
              type="text"
              placeholder="Buscar por nombre..."
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
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

        {/* Filtros avanzados colapsables */}
        <details className="w-full">
          <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-900 font-medium">
            Filtros avanzados
            <svg className="inline w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </summary>
          <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-4 p-4 bg-gray-50 rounded-lg border">
            <div>
              <label className="label text-sm">Fecha desde</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => { setDateFrom(e.target.value); handleFilterChange() }}
                className="input text-sm"
              />
            </div>
            <div>
              <label className="label text-sm">Fecha hasta</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => { setDateTo(e.target.value); handleFilterChange() }}
                className="input text-sm"
              />
            </div>
            <div>
              <label className="label text-sm">Área min (ha)</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                max="10000"
                value={areaMin}
                onChange={(e) => { setAreaMin(e.target.value); handleFilterChange() }}
                className="input text-sm"
                placeholder="0.01"
              />
            </div>
            <div>
              <label className="label text-sm">Área max (ha)</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                max="10000"
                value={areaMax}
                onChange={(e) => { setAreaMax(e.target.value); handleFilterChange() }}
                className="input text-sm"
                placeholder="10000"
              />
            </div>
            <div className="md:col-span-2 lg:col-span-3">
              <label className="label text-sm">Bounding box (min_lon,min_lat,max_lon,max_lat)</label>
              <input
                type="text"
                value={bbox}
                onChange={(e) => { setBbox(e.target.value); handleFilterChange() }}
                className="input text-sm font-mono"
                placeholder="-58.5,-34.5,-58.4,-34.4"
              />
            </div>
          </div>
        </details>
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
              <th className="px-4 py-3 text-left font-medium text-gray-600">Estado</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {lots.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-gray-500">
                  No hay lotes. <Link to="/lots/new" className="text-primary-600 hover:underline">Crea el primero</Link>
                </td>
              </tr>
            ) : (
              lots.map((lot) => {
                const isDeleted = !!lot.deleted_at
                return (
                  <tr key={lot.id} className={`hover:bg-gray-50 ${isDeleted ? 'bg-red-50 line-through' : ''}`}>
                    <td className="px-4 py-3 font-medium text-gray-900">{lot.name}</td>
                    <td className="px-4 py-3 text-gray-600">{lot.area_ha.toFixed(2)}</td>
                    <td className="px-4 py-3 text-gray-500">{new Date(lot.created_at).toLocaleDateString('es-AR')}</td>
                    <td className="px-4 py-3 text-gray-500">{new Date(lot.updated_at).toLocaleDateString('es-AR')}</td>
                    <td className="px-4 py-3">
                      {isDeleted ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
                          Eliminado
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                          Activo
                        </span>
                      )}
                    </td>
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
                        {!isDeleted && onEdit && (
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
                        {!isDeleted ? (
                          <button
                            onClick={() => handleDelete(lot.id)}
                            disabled={deleteMutation.isPending}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition disabled:opacity-50"
                            title="Eliminar (soft delete)"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        ) : (
                          <button
                            onClick={() => handleRestore(lot.id)}
                            disabled={restoreMutation.isPending}
                            className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition disabled:opacity-50"
                            title="Restaurar"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              )}
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
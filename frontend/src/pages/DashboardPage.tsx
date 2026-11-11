// DashboardPage.tsx - Resumen de lotes y análisis del usuario
import { Link } from "react-router-dom"
import { useAuth } from "@/modules/auth/hooks/useAuth"
import { useLots } from "@/modules/lots/hooks/useLots"
import { useAnalyses } from "@/modules/results/hooks/useAnalyses"
import { GROWTH_RATE_UNIT, RESOURCE_LABELS } from "@/types/analysis"
import type { AnalysisRead } from "@/types/analysis"

const STATUS_LABELS: Record<AnalysisRead["status"], { label: string; color: string }> = {
  pending: { label: "Pendiente", color: "bg-yellow-100 text-yellow-700" },
  processing: { label: "Procesando", color: "bg-blue-100 text-blue-700" },
  completed: { label: "Completado", color: "bg-green-100 text-green-700" },
  failed: { label: "Error", color: "bg-red-100 text-red-700" },
}

export const DashboardPage = () => {
  const { user } = useAuth()
  const { data: lotsData, isLoading: lotsLoading } = useLots({ page: 1, size: 100 })
  const { data: analysesData, isLoading: analysesLoading } = useAnalyses({ page: 1, size: 5 })

  const lots = lotsData?.items ?? []
  const totalHa = lots.reduce((sum, lot) => sum + (lot.area_ha || 0), 0)
  const lotNames = Object.fromEntries(lots.map((lot) => [lot.id, lot.name]))
  const analyses = analysesData?.items ?? []

  return (
    <div className="space-y-8">
      {/* Encabezado */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Panel de control</h1>
          <p className="text-gray-600 mt-1">Hola, {user?.full_name || user?.email}</p>
        </div>
        <Link to="/lots/new" className="btn-primary text-center">
          + Nuevo lote
        </Link>
      </div>

      {/* Métricas */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card">
          <div className="text-sm text-gray-600">Lotes activos</div>
          <div className="text-3xl font-bold text-primary-700 mt-1">
            {lotsLoading ? "…" : lotsData?.total ?? 0}
          </div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-600">Superficie total</div>
          <div className="text-3xl font-bold text-primary-700 mt-1">
            {lotsLoading ? "…" : totalHa.toLocaleString("es-AR", { maximumFractionDigits: 1 })}
            <span className="text-base font-medium text-gray-500"> ha</span>
          </div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-600">Análisis realizados</div>
          <div className="text-3xl font-bold text-primary-700 mt-1">
            {analysesLoading ? "…" : analysesData?.total ?? 0}
          </div>
        </div>
      </div>

      {/* Lotes */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">Mis lotes</h2>
          <Link to="/lots" className="text-sm text-primary-600 hover:underline">Ver todos</Link>
        </div>
        {lotsLoading ? (
          <p className="text-gray-500 text-sm">Cargando…</p>
        ) : lots.length === 0 ? (
          <p className="text-gray-500 text-sm">
            Todavía no tenés lotes. <Link to="/lots/new" className="text-primary-600 hover:underline">Creá el primero</Link> dibujándolo en el mapa.
          </p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {lots.slice(0, 5).map((lot) => (
              <li key={lot.id} className="py-3 flex items-center justify-between">
                <div>
                  <Link to={`/lots/${lot.id}`} className="font-medium text-gray-900 hover:text-primary-700">
                    {lot.name}
                  </Link>
                  <div className="text-xs text-gray-500">{lot.area_ha.toFixed(2)} ha</div>
                </div>
                <Link to={`/lots/${lot.id}/analyses`} className="btn-secondary text-sm">
                  Analizar
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Últimos análisis */}
      <div className="card">
        <h2 className="font-semibold text-gray-900 mb-4">Últimos análisis</h2>
        {analysesLoading ? (
          <p className="text-gray-500 text-sm">Cargando…</p>
        ) : analyses.length === 0 ? (
          <p className="text-gray-500 text-sm">
            Todavía no hay análisis. Entrá a un lote y elegí una especie para calcular su tasa de crecimiento.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-left text-gray-600">
                  <th className="px-3 py-2 font-medium">Lote</th>
                  <th className="px-3 py-2 font-medium">Especie</th>
                  <th className="px-3 py-2 font-medium">Tasa promedio</th>
                  <th className="px-3 py-2 font-medium">Estado</th>
                  <th className="px-3 py-2 font-medium">Fecha</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {analyses.map((a) => {
                  const status = STATUS_LABELS[a.status] ?? STATUS_LABELS.pending
                  return (
                    <tr key={a.id} className="hover:bg-gray-50">
                      <td className="px-3 py-2">{lotNames[a.lot_id] ?? "—"}</td>
                      <td className="px-3 py-2">{RESOURCE_LABELS[a.resource_type] ?? a.resource_type}</td>
                      <td className="px-3 py-2 font-medium">
                        {a.status === "completed" ? `${a.average_rate.toFixed(1)} ${GROWTH_RATE_UNIT}` : "—"}
                      </td>
                      <td className="px-3 py-2">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
                          {status.label}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-gray-500">
                        <Link to={`/analyses/${a.id}`} className="hover:underline">
                          {new Date(a.analyzed_at).toLocaleDateString("es-AR")}
                        </Link>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

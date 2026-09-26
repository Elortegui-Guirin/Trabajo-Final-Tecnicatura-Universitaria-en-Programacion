// AnalysisChart - Gráfico de serie temporal con Recharts
import { useTimeSeries } from '@/modules/results/hooks/useAnalyses'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, Legend, BarChart, Bar
} from 'recharts'
import type { ResourceType } from '@/types/analysis'

interface AnalysisChartProps {
  analysisId?: string
  resourceType: ResourceType
  lotName?: string
}

const resourceLabels: Record<ResourceType, string> = {
  resource_1: 'Biomasa verde (kg/ha)',
  resource_2: 'Cobertura suelo (%)',
  resource_3: 'Índice vegetación (NDVI)',
  resource_4: 'Humedad suelo (%)',
}

export function AnalysisChart({ analysisId, resourceType, lotName }: AnalysisChartProps) {
  const { data: timeSeries, isLoading, error } = useTimeSeries(
    analysisId || '', 
    resourceType
  )

  const chartData = timeSeries?.data.map((point) => ({
    date: new Date(point.analyzed_at).toLocaleDateString('es-AR', { 
      day: '2-digit', month: '2-digit', year: '2-digit' 
    }),
    fullDate: point.analyzed_at,
    rate: point.average_rate,
  })) || []

  if (isLoading) {
    return (
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Evolución temporal</h3>
        <div className="h-64 flex items-center justify-center text-gray-500">Cargando gráfico...</div>
      </div>
    )
  }

  if (error || chartData.length === 0) {
    return (
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Evolución temporal</h3>
        <div className="h-64 flex items-center justify-center text-gray-500">
          No hay datos históricos para mostrar
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 className="font-semibold text-gray-900 mb-4">
        Evolución temporal - {resourceLabels[resourceType]}
        {lotName && <span className="text-gray-500 font-normal ml-2">({lotName})</span>}
      </h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12, fill: '#6b7280' }}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis 
              tick={{ fontSize: 12, fill: '#6b7280' }}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'white', 
                border: '1px solid #e5e7eb', 
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
              labelFormatter={(date) => `Fecha: ${date}`}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="rate"
              name={resourceLabels[resourceType]}
              stroke="#16a34a"
              strokeWidth={2}
              dot={{ fill: '#16a34a', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Resumen estadístico */}
      <div className="mt-4 grid gap-4 md:grid-cols-4 text-center">
        <div className="p-3 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-700">
            {chartData[chartData.length - 1]?.rate.toFixed(4) || '—'}
          </div>
          <div className="text-xs text-gray-600">Último valor</div>
        </div>
        <div className="p-3 bg-blue-50 rounded-lg">
          <div className="text-2xl font-bold text-blue-700">
            {Math.max(...chartData.map(d => d.rate)).toFixed(4) || '—'}
          </div>
          <div className="text-xs text-gray-600">Máximo</div>
        </div>
        <div className="p-3 bg-red-50 rounded-lg">
          <div className="text-2xl font-bold text-red-700">
            {Math.min(...chartData.map(d => d.rate)).toFixed(4) || '—'}
          </div>
          <div className="text-xs text-gray-600">Mínimo</div>
        </div>
        <div className="p-3 bg-purple-50 rounded-lg">
          <div className="text-2xl font-bold text-purple-700">
            {(chartData.reduce((a, b) => a + b.rate, 0) / chartData.length).toFixed(4) || '—'}
          </div>
          <div className="text-xs text-gray-600">Promedio histórico</div>
        </div>
      </div>
    </div>
  )
}
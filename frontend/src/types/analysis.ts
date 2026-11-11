// Types para análisis - Extender api.ts existente
export interface AnalysisCreate {
  lot_id: string
  resource_type: ResourceType
}

export type ResourceType = 'resource_1' | 'resource_2' | 'resource_3' | 'resource_4'

// Recursos forrajeros: mapas de tasa de crecimiento de pasturas (kg MS/ha/día).
// Los IDs internos (resource_1..4) no cambian; solo lo que se muestra.
export const RESOURCE_TYPES: ResourceType[] = ['resource_1', 'resource_2', 'resource_3', 'resource_4']

export const RESOURCE_LABELS: Record<ResourceType, string> = {
  resource_1: 'Alfalfa',
  resource_2: 'Festuca',
  resource_3: 'Raigrás',
  resource_4: 'Pastizal natural',
}

export const GROWTH_RATE_UNIT = 'kg MS/ha/día'

// Reexport para los componentes que importan el polígono desde este módulo
export type { GeoJSONPolygon } from './api'

export interface AnalysisRead {
  id: string
  lot_id: string
  resource_type: ResourceType
  average_rate: number
  min_value?: number
  max_value?: number
  std_dev?: number
  percentiles?: Record<string, number>
  raster_file_reference: string
  analyzed_at: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  error_message?: string
}

export interface AnalysisListResponse {
  items: AnalysisRead[]
  total: number
  page: number
  size: number
}

export interface TimeSeriesPoint {
  analyzed_at: string
  average_rate: number
  resource_type: ResourceType
}

export interface TimeSeriesResponse {
  lot_id: string
  resource_type: ResourceType
  data: TimeSeriesPoint[]
}
// Types para análisis - Extender api.ts existente
export interface AnalysisCreate {
  lot_id: string
  resource_type: ResourceType
}

export type ResourceType = 'resource_1' | 'resource_2' | 'resource_3' | 'resource_4'

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
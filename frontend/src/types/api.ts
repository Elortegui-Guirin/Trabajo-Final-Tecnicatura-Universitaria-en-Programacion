// Tipos TypeScript generados desde OpenAPI (placeholder manual)
// En FASE 1 se genera con: make gen-types

export interface UserPublic {
  id: string
  email: string
  full_name: string
  created_at: string
  email_verified: boolean
}

export interface UserRegister {
  email: string
  password: string
  full_name: string
}

export interface UserLogin {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}

export interface TokenRefresh {
  refresh_token: string
}

// === Nuevos tipos para mejoras Fase 2 ===
export interface VerifyEmailRequest {
  token: string
}

export interface ResendVerificationRequest {
  email: string
}

export interface ForgotPasswordRequest {
  email: string
}

export interface ResetPasswordRequest {
  token: string
  new_password: string
  confirm_password: string
}

export interface AuthMessageResponse {
  message: string
}

// === Lotes (Fase 3 + mejoras) ===
export interface LotCreate {
  name: string
  geometry: GeoJSONPolygon
}

export interface LotUpdate {
  name?: string
  geometry?: GeoJSONPolygon
  change_reason?: string
}

export interface GeoJSONPolygon {
  type: 'Polygon'
  coordinates: number[][][] // [exterior_ring, interior_ring*]
}

export interface LotRead {
  id: string
  name: string
  area_ha: number
  geometry: GeoJSONPolygon
  created_at: string
  updated_at: string
  deleted_at?: string
}

export interface LotVersionRead {
  id: string
  lot_id: string
  version_number: number
  name: string
  area_ha: number
  geometry: GeoJSONPolygon
  changed_by: string
  change_reason?: string
  created_at: string
}

export interface LotListResponse {
  items: LotRead[]
  total: number
  page: number
  size: number
}

// Parámetros de búsqueda avanzada
export interface LotSearchParams {
  search?: string
  date_from?: string
  date_to?: string
  area_min?: number
  area_max?: number
  bbox?: string // "min_lon,min_lat,max_lon,max_lat"
  include_deleted?: boolean
}

export type ResourceType = 'resource_1' | 'resource_2' | 'resource_3' | 'resource_4'

export interface AnalysisCreate {
  lot_id: string
  resource_type: ResourceType
}

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
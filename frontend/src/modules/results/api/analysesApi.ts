// Analyses API Client
import api from '@/modules/auth/api/authApi'
import type { 
  AnalysisCreate, 
  AnalysisRead, 
  AnalysisListResponse, 
  TimeSeriesResponse,
  ResourceType 
} from '@/types/analysis'

export const analysesApi = {
  create: (data: AnalysisCreate) => api.post<AnalysisRead>('/analyses', data),
  list: (params?: { 
    lot_id?: string; 
    resource_type?: ResourceType; 
    page?: number; 
    size?: number 
  }) => api.get<AnalysisListResponse>('/analyses', { params }),
  get: (id: string) => api.get<AnalysisRead>(`/analyses/${id}`),
  getTimeSeries: (lotId: string, resourceType: ResourceType) => 
    api.get<TimeSeriesResponse>('/analyses/timeseries', { 
      params: { lot_id: lotId, resource_type: resourceType } 
    }),
  getByLot: (lotId: string, params?: { page?: number; size?: number }) =>
    api.get<AnalysisListResponse>(`/lots/${lotId}/analyses`, { params }),
}
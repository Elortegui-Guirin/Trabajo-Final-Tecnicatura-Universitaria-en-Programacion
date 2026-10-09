// Lots API Client
import api from '@/modules/auth/api/authApi'
import type { 
  LotCreate, LotUpdate, LotRead, LotListResponse, 
  LotVersionRead, LotSearchParams 
} from '@/types/api'

export const lotsApi = {
  create: (data: LotCreate) => api.post<LotRead>('/lots', data),
  list: (params?: LotSearchParams & { page?: number; size?: number }) => 
    api.get<LotListResponse>('/lots', { params }),
  get: (id: string) => api.get<LotRead>(`/lots/${id}`),
  update: (id: string, data: LotUpdate) => api.patch<LotRead>(`/lots/${id}`, data),
  delete: (id: string) => api.delete(`/lots/${id}`),
  restore: (id: string) => api.post<LotRead>(`/lots/${id}/restore`),
  getVersions: (id: string) => api.get<LotVersionRead[]>(`/lots/${id}/versions`),
}
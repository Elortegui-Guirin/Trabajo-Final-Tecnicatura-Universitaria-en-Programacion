// Hooks para análisis - TanStack Query
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { analysesApi } from '@/modules/results/api/analysesApi'
import type { AnalysisCreate, AnalysisRead, AnalysisListResponse, TimeSeriesResponse, ResourceType } from '@/types/analysis'

// Query keys
export const analysisKeys = {
  all: ['analyses'] as const,
  lists: () => [...analysisKeys.all, 'list'] as const,
  list: (params: Record<string, any>) => [...analysisKeys.lists(), params] as const,
  detail: (id: string) => [...analysisKeys.all, 'detail', id] as const,
  timeseries: (lotId: string, resourceType: ResourceType) => 
    [...analysisKeys.all, 'timeseries', lotId, resourceType] as const,
}

export function useAnalyses(params?: { 
  lot_id?: string; 
  resource_type?: ResourceType; 
  page?: number; 
  size?: number 
}) {
  return useQuery({
    queryKey: analysisKeys.list(params || {}),
    queryFn: () => analysesApi.list(params).then((r) => r.data),
    // Mientras haya análisis pendientes o en proceso, volver a consultar cada 2 s
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? []
      return items.some((a) => a.status === 'pending' || a.status === 'processing') ? 2000 : false
    },
  })
}

export function useAnalysis(id: string) {
  return useQuery({
    queryKey: analysisKeys.detail(id),
    queryFn: () => analysesApi.get(id).then((r) => r.data),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'pending' || status === 'processing' ? 2000 : false
    },
  })
}

export function useTimeSeries(lotId: string, resourceType: ResourceType) {
  return useQuery({
    queryKey: analysisKeys.timeseries(lotId, resourceType),
    queryFn: () => analysesApi.getTimeSeries(lotId, resourceType).then((r) => r.data),
    enabled: !!lotId && !!resourceType,
  })
}

export function useCreateAnalysis() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: AnalysisCreate) => analysesApi.create(data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: analysisKeys.lists() })
    },
  })
}

// Polling hook para análisis en progreso
export function useAnalysisPolling(analysisId: string, enabled: boolean) {
  return useQuery({
    queryKey: analysisKeys.detail(analysisId),
    queryFn: () => analysesApi.get(analysisId).then((r) => r.data),
    // TanStack Query v5: refetchInterval recibe la query (no los datos).
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (!status) return 3000
      return status === 'pending' || status === 'processing' ? 3000 : false
    },
    enabled,
  })
}
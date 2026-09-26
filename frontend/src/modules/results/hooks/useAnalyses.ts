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
    queryFn: () => analysesApi.list(params),
  })
}

export function useAnalysis(id: string) {
  return useQuery({
    queryKey: analysisKeys.detail(id),
    queryFn: () => analysesApi.get(id),
    enabled: !!id,
  })
}

export function useTimeSeries(lotId: string, resourceType: ResourceType) {
  return useQuery({
    queryKey: analysisKeys.timeseries(lotId, resourceType),
    queryFn: () => analysesApi.getTimeSeries(lotId, resourceType),
    enabled: !!lotId && !!resourceType,
  })
}

export function useCreateAnalysis() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: AnalysisCreate) => analysesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: analysisKeys.lists() })
    },
  })
}

// Polling hook para análisis en progreso
export function useAnalysisPolling(analysisId: string, enabled: boolean) {
  return useQuery({
    queryKey: analysisKeys.detail(analysisId),
    queryFn: () => analysesApi.get(analysisId),
    refetchInterval: (data) => {
      if (!data) return 3000
      return data.status === 'pending' || data.status === 'processing' ? 3000 : false
    },
    enabled,
  })
}
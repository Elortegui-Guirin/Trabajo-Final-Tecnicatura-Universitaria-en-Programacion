// Hooks para lotes - TanStack Query
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { lotsApi } from '@/modules/lots/api/lotsApi'
import type { LotCreate, LotUpdate, LotRead, LotListResponse } from '@/types/api'

// Query keys
export const lotKeys = {
  all: ['lots'] as const,
  lists: () => [...lotKeys.all, 'list'] as const,
  list: (params: { page?: number; size?: number; search?: string }) => [...lotKeys.lists(), params] as const,
  detail: (id: string) => [...lotKeys.all, 'detail', id] as const,
}

export function useLots(params?: { page?: number; size?: number; search?: string }) {
  return useQuery({
    queryKey: lotKeys.list(params || {}),
    queryFn: () => lotsApi.list(params),
  })
}

export function useLot(id: string) {
  return useQuery({
    queryKey: lotKeys.detail(id),
    queryFn: () => lotsApi.get(id),
    enabled: !!id,
  })
}

export function useCreateLot() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: LotCreate) => lotsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: lotKeys.lists() })
    },
  })
}

export function useUpdateLot() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: LotUpdate }) => lotsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: lotKeys.detail(variables.id) })
      queryClient.invalidateQueries({ queryKey: lotKeys.lists() })
    },
  })
}

export function useDeleteLot() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => lotsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: lotKeys.lists() })
    },
  })
}
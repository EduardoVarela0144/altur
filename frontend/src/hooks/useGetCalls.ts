import { useQuery, UseQueryResult } from '@tanstack/react-query'
import { callsAPI } from '../services/api'
import type { Call, CallsParams } from '../types'

export const useGetCalls = (params: CallsParams = {}): UseQueryResult<Call[], Error> => {
  return useQuery<Call[], Error>({
    queryKey: ['calls', params],
    queryFn: async () => {
      const response = await callsAPI.getCalls(params)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.error || 'Failed to load calls')
    },
    staleTime: 30000, // 30 seconds
  })
}

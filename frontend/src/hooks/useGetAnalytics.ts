import { useQuery, UseQueryResult } from '@tanstack/react-query'
import { callsAPI } from '../services/api'
import type { Analytics } from '../types'

export const useGetAnalytics = (): UseQueryResult<Analytics, Error> => {
  return useQuery<Analytics, Error>({
    queryKey: ['analytics'],
    queryFn: async () => {
      const response = await callsAPI.getAnalytics()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.error || 'Failed to load analytics')
    },
    staleTime: 60000, // 1 minute
  })
}

import { useQuery, UseQueryResult } from '@tanstack/react-query'
import { callsAPI } from '../services/api'
import type { Call } from '../types'

export const useGetCall = (id: string | undefined): UseQueryResult<Call, Error> => {
  return useQuery<Call, Error>({
    queryKey: ['call', id],
    queryFn: async () => {
      if (!id) {
        throw new Error('Call ID is required')
      }
      const response = await callsAPI.getCall(id)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.error || 'Call not found')
    },
    enabled: !!id,
    staleTime: 30000,
  })
}

import { useMutation, useQueryClient, UseMutationResult } from '@tanstack/react-query'
import { callsAPI } from '../services/api'

interface DeleteCallResult {
  success: boolean
  message?: string
  error?: string
}

export const useDeleteCall = (): UseMutationResult<DeleteCallResult, Error, string> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await callsAPI.deleteCall(id)
      if (response.success) {
        return { success: true, message: response.message || 'Call deleted successfully' }
      }
      throw new Error(response.error || 'Delete failed')
    },
    onSuccess: () => {
      // Invalidate and refetch calls list
      queryClient.invalidateQueries({ queryKey: ['calls'] })
    },
  })
}

import { useMutation, useQueryClient, UseMutationResult } from '@tanstack/react-query'
import { callsAPI } from '../services/api'
import type { Call } from '../types'

interface UploadCallResult {
  success: boolean
  data?: Call
  error?: string
}

export const useUploadCall = (): UseMutationResult<UploadCallResult, Error, File> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (file: File) => {
      const response = await callsAPI.uploadCall(file)
      if (response.success && response.data) {
        return { success: true, data: response.data }
      }
      throw new Error(response.error || 'Upload failed')
    },
    onSuccess: () => {
      // Invalidate and refetch calls list
      queryClient.invalidateQueries({ queryKey: ['calls'] })
    },
  })
}

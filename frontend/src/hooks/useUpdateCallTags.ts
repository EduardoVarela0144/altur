import { useMutation, useQueryClient, UseMutationResult } from '@tanstack/react-query'
import { callsAPI } from '../services/api'
import type { Call } from '../types'

interface UpdateTagsResult {
  success: boolean
  data?: Call
  error?: string
}

export const useUpdateCallTags = (): UseMutationResult<UpdateTagsResult, Error, { id: string; tags: string[] }> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, tags }: { id: string; tags: string[] }) => {
      const response = await callsAPI.updateCallTags(id, tags)
      if (response.success && response.data) {
        return { success: true, data: response.data }
      }
      throw new Error(response.error || 'Failed to update tags')
    },
    onSuccess: (_, variables) => {
      // Invalidate and refetch calls list and specific call
      queryClient.invalidateQueries({ queryKey: ['calls'] })
      queryClient.invalidateQueries({ queryKey: ['call', variables.id] })
    },
  })
}


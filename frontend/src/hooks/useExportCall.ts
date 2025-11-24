import { useMutation, UseMutationResult } from '@tanstack/react-query'
import { callsAPI } from '../services/api'

interface ExportCallResult {
  success: boolean
  message?: string
  error?: string
}

export const useExportCall = (): UseMutationResult<ExportCallResult, Error, string> => {
  return useMutation({
    mutationFn: async (id: string) => {
      const blob = await callsAPI.exportCall(id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `call_${id}.json`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      return { success: true, message: 'Call exported successfully' }
    },
  })
}

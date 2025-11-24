import axios, { AxiosInstance } from 'axios'
import type { Call, ApiResponse, Analytics, CallsParams } from '../types'

// Use localhost:5000 directly since backend is exposed on host port 5000
// This works both in Docker (backend is exposed) and local dev
const API_BASE_URL = 'http://localhost:5000'

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error
      console.error('API Error:', error.response.data)
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.request)
    } else {
      // Something else happened
      console.error('Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export const callsAPI = {
  // Upload and process a call
  uploadCall: async (file: File, sessionId?: string): Promise<ApiResponse<Call>> => {
    const formData = new FormData()
    formData.append('file', file)
    if (sessionId) {
      formData.append('session_id', sessionId)
    }

    const response = await api.post<ApiResponse<Call>>('/api/calls', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Get all calls
  getCalls: async (params: CallsParams = {}): Promise<ApiResponse<Call[]>> => {
    const response = await api.get<ApiResponse<Call[]>>('/api/calls', { params })
    return response.data
  },

  // Get single call
  getCall: async (id: string): Promise<ApiResponse<Call>> => {
    const response = await api.get<ApiResponse<Call>>(`/api/calls/${id}`)
    return response.data
  },

  // Delete call
  deleteCall: async (id: string): Promise<ApiResponse<void>> => {
    const response = await api.delete<ApiResponse<void>>(`/api/calls/${id}`)
    return response.data
  },

  // Update/override tags
  updateCallTags: async (id: string, tags: string[]): Promise<ApiResponse<Call>> => {
    const response = await api.put<ApiResponse<Call>>(`/api/calls/${id}/tags`, { tags })
    return response.data
  },

  // Export call as JSON
  exportCall: async (id: string): Promise<Blob> => {
    const response = await api.get(`/api/calls/${id}/export`, {
      responseType: 'blob',
    })
    return response.data
  },

  // Get analytics
  getAnalytics: async (): Promise<ApiResponse<Analytics>> => {
    const response = await api.get<ApiResponse<Analytics>>('/api/calls/analytics')
    return response.data
  },
}

export default api

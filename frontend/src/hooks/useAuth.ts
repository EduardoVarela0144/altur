import { useState, useEffect } from 'react'
import { useMutation, UseMutationResult } from '@tanstack/react-query'
import axios from 'axios'
import { API_BASE_URL } from '../config'

interface LoginData {
  username: string
  password: string
}

interface RegisterData {
  username: string
  password: string
  email?: string
}

interface AuthResponse {
  success: boolean
  data?: {
    user_id: string
    username: string
    email?: string
    token: string
    expires_at: string
  }
  error?: string
}

export const useAuth = () => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('auth_token'))
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    if (token) {
      // Set default authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } else {
      delete axios.defaults.headers.common['Authorization']
    }
  }, [token])

  const loginMutation: UseMutationResult<AuthResponse, Error, LoginData> = useMutation({
    mutationFn: async (data: LoginData) => {
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, data)
      return response.data
    },
    onSuccess: (data) => {
      if (data.success && data.data) {
        setToken(data.data.token)
        setUser({ id: data.data.user_id, username: data.data.username, email: data.data.email })
        localStorage.setItem('auth_token', data.data.token)
        axios.defaults.headers.common['Authorization'] = `Bearer ${data.data.token}`
      }
    },
  })

  const registerMutation: UseMutationResult<AuthResponse, Error, RegisterData> = useMutation({
    mutationFn: async (data: RegisterData) => {
      const response = await axios.post(`${API_BASE_URL}/api/auth/register`, data)
      return response.data
    },
  })

  const logoutMutation: UseMutationResult<any, Error, void> = useMutation({
    mutationFn: async () => {
      try {
        const response = await axios.post(`${API_BASE_URL}/api/auth/logout`)
        return response.data
      } catch (error) {
        // Even if API call fails, we still want to clear local state
        console.warn('Logout API call failed, but clearing local state anyway:', error)
        return { success: true }
      }
    },
    onSuccess: () => {
      setToken(null)
      setUser(null)
      localStorage.removeItem('auth_token')
      delete axios.defaults.headers.common['Authorization']
    },
  })

  const login = (username: string, password: string) => {
    return loginMutation.mutateAsync({ username, password })
  }

  const register = (username: string, password: string, email?: string) => {
    return registerMutation.mutateAsync({ username, password, email })
  }

  const logout = () => {
    return logoutMutation.mutateAsync()
  }

  return {
    user,
    token,
    isAuthenticated: !!token,
    login,
    register,
    logout,
    loginLoading: loginMutation.isPending,
    registerLoading: registerMutation.isPending,
    logoutLoading: logoutMutation.isPending,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
  }
}


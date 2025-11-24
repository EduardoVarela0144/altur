import { useState, useEffect, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { websocketService, ProgressUpdate, UploadComplete } from '../services/websocket'
import { callsAPI } from '../services/api'
import type { Call } from '../types'

// Simple UUID generator (no need for external library)
const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

interface UploadProgress {
  stage: string
  progress: number
  message: string
  elapsedTime?: number // Time elapsed in seconds
  estimatedTimeRemaining?: number // Estimated time remaining in seconds
}

interface UseUploadCallWithProgressResult {
  upload: (file: File) => Promise<void>
  progress: UploadProgress | null
  isUploading: boolean
  error: string | null
  result: Call | null
}

export const useUploadCallWithProgress = (): UseUploadCallWithProgressResult => {
  const [progress, setProgress] = useState<UploadProgress | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<Call | null>(null)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [startTime, setStartTime] = useState<number | null>(null)
  const queryClient = useQueryClient()

  // Update elapsed time every second while uploading
  useEffect(() => {
    if (!isUploading || !startTime) return

    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000)
      const currentProgress = progress?.progress ?? 0
      
      // Calculate estimated remaining time
      let estimatedRemaining: number | undefined = undefined
      if (currentProgress > 0 && elapsed > 0) {
        const totalEstimated = Math.floor((elapsed * 100) / currentProgress)
        estimatedRemaining = Math.max(0, totalEstimated - elapsed)
      }
      
      setProgress((prev) => {
        if (!prev) return null
        return {
          ...prev,
          elapsedTime: elapsed,
          estimatedTimeRemaining: estimatedRemaining,
        }
      })
    }, 1000) // Update every second

    return () => clearInterval(interval)
  }, [isUploading, startTime, progress?.progress])

  useEffect(() => {
    // Connect to WebSocket on mount
    const socket = websocketService.connect()
    
    // Listen for progress updates
    const handleProgress = (data: ProgressUpdate) => {
      console.log('[Upload] Progress update received:', data, 'Current session:', currentSessionId)
      // Only process if session_id matches current upload or if no current session (initial state)
      if (!currentSessionId || data.session_id === currentSessionId) {
        // Calculate elapsed time and estimated remaining time
        const now = Date.now()
        const elapsed = startTime ? Math.floor((now - startTime) / 1000) : 0
        const currentProgress = Math.max(0, Math.min(100, data.progress))
        
        // Estimate remaining time based on current progress
        // Only calculate if we have progress > 0 and elapsed time > 0
        let estimatedRemaining: number | undefined = undefined
        if (currentProgress > 0 && elapsed > 0) {
          const totalEstimated = Math.floor((elapsed * 100) / currentProgress)
          estimatedRemaining = Math.max(0, totalEstimated - elapsed)
        }
        
        // Update progress immediately to ensure UI reflects changes
        setProgress((prev) => {
          // Only update if new progress is higher or if it's a different stage
          if (!prev || data.progress > prev.progress || data.stage !== prev.stage) {
            return {
              stage: data.stage,
              progress: currentProgress,
              message: data.message || prev?.message || 'Processing...',
              elapsedTime: elapsed,
              estimatedTimeRemaining: estimatedRemaining,
            }
          }
          // Update time even if progress hasn't changed
          return {
            ...prev,
            elapsedTime: elapsed,
            estimatedTimeRemaining: estimatedRemaining,
          }
        })
      }
    }

    // Listen for completion
    const handleComplete = (data: UploadComplete) => {
      console.log('[Upload] Complete event received:', data, 'Current session:', currentSessionId)
      // Only process if session_id matches current upload
      if (!currentSessionId || data.session_id === currentSessionId) {
        if (data.success && data.data) {
          const totalTime = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0
          setResult(data.data)
          setProgress({
            stage: 'complete',
            progress: 100,
            message: 'Upload complete!',
            elapsedTime: totalTime,
            estimatedTimeRemaining: 0,
          })
          setIsUploading(false)
          setCurrentSessionId(null)
          setStartTime(null)
          // Invalidate and refetch calls list
          queryClient.invalidateQueries({ queryKey: ['calls'] })
        } else {
          setError(data.error || 'Upload failed')
          setIsUploading(false)
          setProgress(null)
          setCurrentSessionId(null)
          setStartTime(null)
        }
      }
    }

    // Register listeners
    websocketService.on('upload_progress', handleProgress)
    websocketService.on('upload_complete', handleComplete)
    
    // Re-register listeners on reconnect
    const handleReconnect = () => {
      console.log('[Upload] WebSocket reconnected, re-registering listeners and rejoining room')
      // Re-register listeners (they should be preserved, but ensure they're active)
      websocketService.on('upload_progress', handleProgress)
      websocketService.on('upload_complete', handleComplete)
      // Re-join room if we're currently uploading
      if (currentSessionId && websocketService.isConnected()) {
        setTimeout(() => {
          websocketService.joinRoom(currentSessionId)
          console.log(`[Upload] Rejoined room ${currentSessionId} after reconnect`)
        }, 500)
      }
    }
    
    socket.on('reconnect', handleReconnect)
    socket.on('connect', handleReconnect) // Also handle initial connect

    return () => {
      websocketService.off('upload_progress', handleProgress)
      websocketService.off('upload_complete', handleComplete)
      socket.off('reconnect', handleReconnect)
    }
  }, [queryClient, currentSessionId, startTime])

  const upload = useCallback(async (file: File) => {
    // Generate session ID
    const sessionId = generateUUID()
    console.log('[Upload] Starting upload with session ID:', sessionId)
    
    // Reset state
    setProgress(null)
    setError(null)
    setResult(null)
    setIsUploading(true)
    setCurrentSessionId(sessionId) // Store current session ID
    setStartTime(Date.now()) // Record start time

    try {
      // Ensure WebSocket is connected
      if (!websocketService.isConnected()) {
        console.log('[Upload] Connecting to WebSocket...')
        websocketService.connect()
        // Wait for connection
        await new Promise((resolve) => {
          const socket = websocketService.connect()
          if (socket.connected) {
            resolve(undefined)
          } else {
            socket.once('connect', () => {
              console.log('[Upload] WebSocket connected')
              resolve(undefined)
            })
            // Timeout after 3 seconds
            setTimeout(() => resolve(undefined), 3000)
          }
        })
      }

      // Ensure we're connected before joining room
      let attempts = 0
      while (!websocketService.isConnected() && attempts < 10) {
        console.log(`[Upload] Waiting for WebSocket connection (attempt ${attempts + 1})...`)
        await new Promise(resolve => setTimeout(resolve, 500))
        attempts++
      }
      
      if (!websocketService.isConnected()) {
        throw new Error('WebSocket connection failed. Please refresh the page.')
      }
      
      // Join WebSocket room - wait a bit to ensure connection is stable
      await new Promise(resolve => setTimeout(resolve, 200))
      console.log('[Upload] Joining room:', sessionId)
      websocketService.joinRoom(sessionId)
      
      // Wait a bit more to ensure join is processed by server
      await new Promise(resolve => setTimeout(resolve, 500))
      
      console.log('[Upload] Room joined, starting upload...')

      // Set initial progress
      setProgress({
        stage: 'uploading',
        progress: 0,
        message: 'Preparing upload...',
      })

      // Upload file
      console.log('[Upload] Uploading file...')
      const response = await callsAPI.uploadCall(file, sessionId)
      
      console.log('[Upload] Upload response:', response)
      
      if (!response.success) {
        throw new Error(response.error || 'Upload failed')
      }

      // Progress updates will come via WebSocket
      // The upload_complete event will be handled by the useEffect
    } catch (err: any) {
      console.error('[Upload] Error:', err)
      setError(err.message || 'Upload failed')
      setIsUploading(false)
      setProgress(null)
      setStartTime(null)
    }
  }, [])

  return {
    upload,
    progress,
    isUploading,
    error,
    result,
  }
}


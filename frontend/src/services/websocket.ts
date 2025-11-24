import { io, Socket } from 'socket.io-client'

const WS_URL = 'http://localhost:5000'

export interface ProgressUpdate {
  session_id: string
  stage: 'uploading' | 'processing' | 'transcribing' | 'analyzing' | 'saving' | 'complete' | 'error'
  progress: number
  message: string
}

export interface UploadComplete {
  session_id: string
  success: boolean
  data?: any
  error?: string
}

class WebSocketService {
  private socket: Socket | null = null
  private listeners: Map<string, Set<Function>> = new Map()

  connect(): Socket {
    if (this.socket?.connected) {
      return this.socket
    }

    this.socket = io(WS_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity, // Keep trying to reconnect
      timeout: 20000,
      forceNew: false,
    })

    this.socket.on('connect', () => {
      console.log('[WebSocket] Connected to server')
      // Re-register all listeners after reconnection
      this.listeners.forEach((callbacks, event) => {
        this.socket?.on(event, (data: any) => {
          console.log(`[WebSocket] Received event: ${event}`, data)
          callbacks.forEach((cb) => cb(data))
        })
      })
    })

    this.socket.on('disconnect', (reason) => {
      console.log('[WebSocket] Disconnected from server. Reason:', reason)
      // Will automatically reconnect due to reconnection: true
    })

    this.socket.on('reconnect', (attemptNumber) => {
      console.log(`[WebSocket] Reconnected after ${attemptNumber} attempts`)
    })

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`[WebSocket] Reconnection attempt ${attemptNumber}`)
    })

    this.socket.on('reconnect_error', (error) => {
      console.error('[WebSocket] Reconnection error:', error)
    })

    this.socket.on('reconnect_failed', () => {
      console.error('[WebSocket] Reconnection failed after all attempts')
    })

    this.socket.on('connected', (data) => {
      console.log('[WebSocket] Server confirmation:', data)
    })

    return this.socket
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.listeners.clear()
  }

  on(event: string, callback: Function): void {
    if (!this.socket || !this.socket.connected) {
      this.connect()
    }

    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
      // Set up the socket listener only once per event
      if (this.socket) {
        this.socket.on(event, (data: any) => {
          console.log(`[WebSocket] Received event: ${event}`, data)
          this.listeners.get(event)?.forEach((cb) => cb(data))
        })
      }
    }

    this.listeners.get(event)!.add(callback)
  }

  off(event: string, callback?: Function): void {
    if (callback && this.listeners.has(event)) {
      this.listeners.get(event)!.delete(callback)
    } else {
      this.listeners.delete(event)
    }

    if (this.socket && !callback) {
      this.socket.off(event)
    }
  }

  joinRoom(room: string): void {
    if (this.socket && this.socket.connected) {
      this.socket.emit('join', room)
      console.log(`[WebSocket] Emitted join for room: ${room}`)
    } else {
      console.warn(`[WebSocket] Cannot join room ${room}: socket not connected. Will retry on reconnect.`)
      // Store room to join on reconnect
      const storedRoom = room
      if (!this.socket) {
        this.connect()
      }
      // Try to join when reconnected
      const reconnectHandler = () => {
        if (this.socket && this.socket.connected) {
          this.socket.emit('join', storedRoom)
          console.log(`[WebSocket] Joined room after reconnect: ${storedRoom}`)
          this.socket.off('connect', reconnectHandler)
        }
      }
      if (this.socket) {
        this.socket.once('connect', reconnectHandler)
      }
    }
  }

  isConnected(): boolean {
    return this.socket?.connected ?? false
  }
}

export const websocketService = new WebSocketService()


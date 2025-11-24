// Centralized configuration for API and WebSocket URLs
// Uses environment variables with fallback to localhost for local development

// In production (Render), set VITE_API_URL to your backend URL
// Example: https://your-backend.onrender.com
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

// WebSocket URL - same as API URL but with ws:// or wss:// protocol
const getWebSocketUrl = (apiUrl: string): string => {
  if (apiUrl.startsWith('https://')) {
    return apiUrl.replace('https://', 'wss://')
  } else if (apiUrl.startsWith('http://')) {
    return apiUrl.replace('http://', 'ws://')
  }
  return apiUrl
}

export const API_BASE_URL = API_URL
export const WS_URL = getWebSocketUrl(API_URL)

console.log('[Config] API URL:', API_BASE_URL)
console.log('[Config] WebSocket URL:', WS_URL)


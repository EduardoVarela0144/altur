import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  // In Docker Compose, use 'backend' as the hostname
  // In local dev, use localhost
  // In production (Render), the proxy is not used - API calls go directly to VITE_API_URL
  const backendUrl = process.env.DOCKER_ENV 
    ? 'http://backend:5000' 
    : 'http://localhost:5000'
  
  console.error(`[Vite Config] Proxy target: ${backendUrl}`)

  return {
    plugins: [react()],
    server: {
      host: true,
      port: 5173,
      proxy: {
        '/api': {
          target: backendUrl,
          changeOrigin: true,
          secure: false,
          ws: false,
          configure: (proxy, options) => {
            // Ensure we're using the correct target
            console.error('[Proxy Configure] Target:', options.target)
            console.error('[Proxy Configure] Host:', options.host)
            
            proxy.on('error', (err, req, res) => {
              console.error('[Proxy Error]', err.message);
              console.error('[Proxy Error] Code:', err.code);
              console.error('[Proxy Error] Target:', options.target);
            });
            proxy.on('proxyReq', (proxyReq, req, res) => {
              console.error(`[Proxy Request] ${req.method} ${req.url} -> ${options.target}${req.url}`);
            });
          },
        },
      },
    },
    resolve: {
      alias: {
        '@components': path.resolve(__dirname, './src/components'),
        '@pages': path.resolve(__dirname, './src/pages'),
        '@services': path.resolve(__dirname, './src/services'),
        '@hooks': path.resolve(__dirname, './src/hooks'),
        '@types': path.resolve(__dirname, './src/types'),
      },
      dedupe: ['@mui/x-date-pickers'],
    },
    optimizeDeps: {
      include: ['date-fns'],
      exclude: ['@mui/x-date-pickers'],
      esbuildOptions: {
        plugins: [],
      },
    },
  }
})


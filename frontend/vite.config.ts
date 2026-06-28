import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    hmr: {
      // Browser connects HMR WebSocket to nginx on port 80,
      // nginx proxies it to Vite on 5173 inside Docker.
      clientPort: 80,
    },
  },
})
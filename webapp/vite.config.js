import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/analyze': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/inference': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/checkpoints': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  }
})

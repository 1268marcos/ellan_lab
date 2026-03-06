import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/sp': {
        target: 'http://localhost:8201',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/sp/, ''),
      },
      '/api/pt': {
        target: 'http://localhost:8202',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/pt/, ''),
      },
      '/api/gw': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/gw/, ''),
      },
      '/api/op': {
        target: 'http://localhost:8003',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/op/, ''),
      },
    },
  },
})
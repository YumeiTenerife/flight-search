import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    extensions: ['.jsx', '.js', '.json']
  },
  server: {
    port: 3000,
    proxy: {
      '/search': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/autocomplete': 'http://localhost:8000',
      '/price-calendar': 'http://localhost:8000',
      '/alerts': 'http://localhost:8000',
    }
  }
})

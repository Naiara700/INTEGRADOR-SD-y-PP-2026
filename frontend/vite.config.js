import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Captura todo lo que empiece con /proxy-api
      '/proxy-api': {
        target: 'https://34.71.7.126',
        secure: false, // Por si el certificado SSL está recién creándose
        headers: {
          Host: 'api.stickerchain.lat'
        },
        rewrite: (path) => path.replace(/^\/proxy-api/, '') // Le quita el /proxy-api antes de mandarlo al backend
      }
    }
  }
})

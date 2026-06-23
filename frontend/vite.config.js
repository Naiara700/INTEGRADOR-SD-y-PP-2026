import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Captura todo lo que empiece con /proxy-api
      '/proxy-api': {
        target: 'https://api.stickerchain.lat',
        changeOrigin: true,
        secure: false, // Por si el certificado SSL está recién creándose
        rewrite: (path) => path.replace(/^\/proxy-api/, '') // Le quita el /proxy-api antes de mandarlo al backend
      }
    }
  }
})

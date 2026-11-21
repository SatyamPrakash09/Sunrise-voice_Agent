import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  envPrefix: ['VITE_', 'BACKEND_'],
  server: {
    proxy: {
      '/token': 'http://localhost:3000',
    },
  },
})
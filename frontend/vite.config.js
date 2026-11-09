import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// En desarrollo, Vite corre en :5173 y reenvía /api al backend en :8000.
// En producción no hace falta: FastAPI sirve el build desde el mismo origen.
export default defineConfig({
  plugins: [react()],
  build: { chunkSizeWarningLimit: 800 }, // recharts pesa; para este proyecto no vale la pena dividir
  server: {
    host: true, // permite abrir la app desde el teléfono en la misma red (para probar el QR)
    proxy: { '/api': 'http://localhost:8000' },
  },
})

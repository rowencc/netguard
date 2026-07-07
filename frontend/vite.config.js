import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3099,
    proxy: {
      '/api': {
        target: 'http://localhost:8089',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8089',
        ws: true
      }
    }
  }
})

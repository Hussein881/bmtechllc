import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/bmtechllc/' : '/',
  plugins: [react()],
  build: {
    target: 'es2020',
    cssCodeSplit: false,
  },
}))

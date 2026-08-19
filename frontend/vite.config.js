import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const BACKEND = 'http://127.0.0.1:8001'

// Several paths (e.g. /patients/:id, /admin) exist both as SPA routes and as
// content-negotiated JSON endpoints on the backend (see Phase 7 notes in
// PROGRESS.md): the same URL returns HTML for a browser navigation, JSON when
// Accept: application/json is sent. Our own api.js always sends that header,
// so this bypass lets a real browser navigation (hard refresh, typed URL)
// fall through to Vite's own SPA history-fallback instead of hitting FastAPI.
const jsonOnly = {
  target: BACKEND,
  changeOrigin: true,
  bypass(req) {
    if (!(req.headers.accept || '').includes('application/json')) {
      return req.url
    }
  },
}

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/auth': jsonOnly,
      '/logout': jsonOnly,
      '/patients': jsonOnly,
      '/admin': jsonOnly,
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
    globals: true,
  },
})

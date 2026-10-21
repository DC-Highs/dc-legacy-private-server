import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

const backend = process.env.VITE_BACKEND_URL ?? "http://127.0.0.1:8080"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": path.resolve(import.meta.dirname, "src") },
  },
  build: {
    // "assets" is already the URL of the game's own files, served by the backend.
    assetsDir: "_app",
  },
  server: {
    proxy: {
      "/api": backend,
      "/static": backend,
      "/flash": backend,
      "/assets": backend,
      "/deploy": backend,
      "/stream": backend,
    },
  },
})

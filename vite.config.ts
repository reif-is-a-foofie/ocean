import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  root: "ui",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:7777",
      "/healthz": "http://127.0.0.1:7777"
    }
  },
  build: {
    outDir: "dist",
    emptyOutDir: true
  }
});

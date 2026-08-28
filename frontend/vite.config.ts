import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  server: {
    port: 5173,
    strictPort: false,
    open: "/",
    proxy: {
      // Must match scripts/dev.ps1 ($DevApiPort). Do not use 8080 — stale zombies on Windows.
      "/api/v1": { target: "http://127.0.0.1:8088", changeOrigin: true },
    },
  },
  optimizeDeps: {
    exclude: ["mermaid"],
  },
});

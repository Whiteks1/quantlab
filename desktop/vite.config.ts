import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

export default defineConfig({
  plugins: [react()],
  root: resolve(__dirname, "renderer"),
  base: "./",
  build: {
    outDir: resolve(__dirname, "renderer", "dist"),
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, "renderer", "index.html"),
    },
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
  },
});

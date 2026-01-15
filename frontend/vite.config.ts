// C:\Users\Vinay\Project\frontend\vite.config.ts
// --- SIMPLIFIED AND CORRECTED VERSION ---

import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // We can still load env if other parts of your build process need it.
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [vue(), vueDevTools()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    // --- THIS IS THE FIX ---
    server: {
      // 'true' is the modern alias for '0.0.0.0' and enables auto-detection
      // for the HMR client, which is what we need.
      host: true,
      port: 5173, // Keep the port consistent
    },
    // By removing the explicit 'hmr' block, we allow Vite to automatically
    // configure the client to use the correct network IP instead of 'localhost'.
  }
})

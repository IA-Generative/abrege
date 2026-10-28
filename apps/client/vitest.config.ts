import { fileURLToPath } from 'node:url'
import { configDefaults, defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      // Playwright specs live under playwright/e2e and need a browser plus a running stack: they run through `test:e2e-ci`, not Vitest.
      exclude: [...configDefaults.exclude, 'playwright/**'],
      root: fileURLToPath(new URL('./', import.meta.url)),
      setupFiles: [
        fileURLToPath(new URL('./vitest-setup.ts', import.meta.url)),
      ],
    },
  }),
)

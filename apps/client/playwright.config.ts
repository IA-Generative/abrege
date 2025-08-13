import process from 'node:process'
import { defineConfig, devices } from '@playwright/test'

import dotenv from 'dotenv'

dotenv.config({ path: '../../.env' })

export default defineConfig({
  testDir: './playwright/e2e',
  timeout: 30 * 1000,
  expect: {
    timeout: 5000
  },
  use: {
    actionTimeout: 60000,
    navigationTimeout: 60000,
    baseURL: `http://localhost:3000`,
    trace: 'on-first-retry',
    headless: true,
  },

  projects: [
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox']
      }
    },
  ],

  /* Folder for test artifacts such as screenshots, videos, traces, etc. */
  // outputDir: 'test-results/',

  webServer: {
    command: 'pnpm run dev',
    port: Number(process.env.FRONT_PORT),
  }
})

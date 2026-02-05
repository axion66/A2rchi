import { defineConfig, devices } from '@playwright/test';

/**
 * Root Playwright configuration for running UI tests from the project root.
 * 
 * Usage: npx playwright test
 * 
 * This config points to the same tests as tests/playwright.config.ts but allows
 * running from the project root directory.
 */
export default defineConfig({
  testDir: './tests/ui',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  timeout: 30_000,
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:2786',
    trace: 'on-first-retry',
    headless: true,
    viewport: { width: 1440, height: 900 },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});

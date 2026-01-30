import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './ui',
  timeout: 30_000,
  retries: 0,
  use: {
    baseURL: 'http://localhost:2786',
    headless: true,
    viewport: { width: 1440, height: 900 },
  },
});

import { defineConfig, devices } from '@playwright/test';

import { getPlaywrightEnv } from './tests/harness/env';

const env = getPlaywrightEnv();
const isCI = env.flags.isCI;
const skipWebServer = env.flags.skipWebServer;

const realBaseUrl = env.baseUrl;
const mockBaseUrl = env.mockBaseUrl;

const isLocalUrl = (url: string) => url.startsWith('http://localhost') || url.startsWith('http://127.0.0.1');

const shouldStartWebServers = !skipWebServer && isLocalUrl(realBaseUrl) && isLocalUrl(mockBaseUrl);

const parsePort = (url: string, fallback: number) => {
  try {
    const parsed = new URL(url);
    if (parsed.port) return Number(parsed.port);
    return parsed.protocol === 'https:' ? 443 : 80;
  } catch {
    return fallback;
  }
};

const realPort = parsePort(realBaseUrl, 3000);
const mockPort = parsePort(mockBaseUrl, 3001);

const realCommand = isCI ? `pnpm build && pnpm start -p ${realPort}` : `pnpm dev --port ${realPort}`;
const mockCommand = isCI ? `pnpm build && pnpm start -p ${mockPort}` : `pnpm dev --port ${mockPort}`;

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  retries: 0,
  globalSetup: './tests/global-setup.ts',
  use: {
    trace: 'on-first-retry',
  },
  webServer: shouldStartWebServers
    ? [
        {
          name: 'web-app',
          command: realCommand,
          url: realBaseUrl,
          reuseExistingServer: !isCI,
          timeout: 120_000,
        },
        {
          name: 'web-app-mock',
          command: mockCommand,
          url: mockBaseUrl,
          reuseExistingServer: !isCI,
          timeout: 120_000,
          env: {
            NEXT_PUBLIC_AGENT_API_MOCK: 'true',
            NEXT_DIST_DIR: '.next-mock',
          },
        },
      ]
    : undefined,
  projects: [
    {
      name: 'chromium-real',
      use: { ...devices['Desktop Chrome'], baseURL: realBaseUrl },
      testIgnore: ['**/*.mock.spec.ts'],
    },
    {
      name: 'chromium-mock',
      use: { ...devices['Desktop Chrome'], baseURL: mockBaseUrl },
      testMatch: ['**/*.mock.spec.ts'],
    },
  ],
});

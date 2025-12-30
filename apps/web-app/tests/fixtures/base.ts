import { expect, test as base, type Page, type TestInfo } from '@playwright/test';

import { getPlaywrightEnv, type PlaywrightEnv } from '../harness/env';
import { getStorageStatePath, type StorageStateMode } from '../harness/storageState';

interface TestFixtures {
  tenantAdminPage: Page;
  operatorPage: Page;
}

interface WorkerFixtures {
  env: PlaywrightEnv;
  apiBaseUrl: string;
}

function resolveMode(testInfo: TestInfo): StorageStateMode {
  return testInfo.project.name.includes('mock') ? 'mock' : 'real';
}

function resolveBaseUrl(testInfo: TestInfo, env: PlaywrightEnv, mode: StorageStateMode): string {
  const projectBase = (testInfo.project.use as { baseURL?: string } | undefined)?.baseURL;
  if (projectBase) {
    return projectBase;
  }
  return mode === 'mock' ? env.mockBaseUrl : env.baseUrl;
}

export const test = base.extend<TestFixtures, WorkerFixtures>({
  env: [
    async ({}, provide) => {
      await provide(getPlaywrightEnv());
    },
    { scope: 'worker' },
  ],
  apiBaseUrl: [
    async ({ env }, provide) => {
      await provide(env.apiBaseUrl);
    },
    { scope: 'worker' },
  ],
  tenantAdminPage: async ({ browser, env }, provide, testInfo) => {
    const mode = resolveMode(testInfo);
    const baseURL = resolveBaseUrl(testInfo, env, mode);
    const storageState = getStorageStatePath('tenant-admin', mode);

    const context = await browser.newContext({ baseURL, storageState });
    const page = await context.newPage();
    await provide(page);
    await context.close();
  },
  operatorPage: async ({ browser, env }, provide, testInfo) => {
    const mode = resolveMode(testInfo);
    const baseURL = resolveBaseUrl(testInfo, env, mode);
    const storageState = getStorageStatePath('operator', mode);

    const context = await browser.newContext({ baseURL, storageState });
    const page = await context.newPage();
    await provide(page);
    await context.close();
  },
});

export { expect };

import type { FullConfig } from '@playwright/test';

import { getPlaywrightEnv } from './harness/env';
import { getSelectedProjects, shouldRunProject } from './harness/projects';
import { ensureFixtures } from './harness/seed';
import { ensureStorageState, getStorageStatePath } from './harness/storageState';

export default async function globalSetup(config: FullConfig) {
  const env = getPlaywrightEnv();
  const selectedProjects = getSelectedProjects(process.argv);

  const realProject = config.projects.find((project) => project.name === 'chromium-real');
  const mockProject = config.projects.find((project) => project.name === 'chromium-mock');
  const realBaseUrl = (realProject?.use?.baseURL as string | undefined) ?? env.baseUrl;
  const mockBaseUrl = (mockProject?.use?.baseURL as string | undefined) ?? env.mockBaseUrl;

  const runReal = shouldRunProject(selectedProjects, 'chromium-real');
  const runMock = shouldRunProject(selectedProjects, 'chromium-mock');

  if (runReal) {
    await ensureFixtures({
      shouldSeed: env.flags.seedOnStart || env.flags.isCI,
      skipSeed: env.flags.skipSeed,
      apiBaseUrl: env.apiBaseUrl,
    });
  }

  const refreshStorage = env.flags.refreshStorageState || env.flags.isCI;
  const skipStorage = env.flags.skipStorageState;

  if (runReal) {
    await ensureStorageState({
      baseURL: realBaseUrl,
      storagePath: getStorageStatePath('tenant-admin', 'real'),
      email: env.tenantAdmin.email,
      password: env.tenantAdmin.password,
      refresh: refreshStorage,
      skip: skipStorage,
    });

    await ensureStorageState({
      baseURL: realBaseUrl,
      storagePath: getStorageStatePath('operator', 'real'),
      email: env.operator.email,
      password: env.operator.password,
      refresh: refreshStorage,
      skip: skipStorage,
    });
  }

  if (runMock) {
    await ensureStorageState({
      baseURL: mockBaseUrl,
      storagePath: getStorageStatePath('tenant-admin', 'mock'),
      email: env.tenantAdmin.email,
      password: env.tenantAdmin.password,
      refresh: true,
      skip: skipStorage,
    });

    await ensureStorageState({
      baseURL: mockBaseUrl,
      storagePath: getStorageStatePath('operator', 'mock'),
      email: env.operator.email,
      password: env.operator.password,
      refresh: true,
      skip: skipStorage,
    });
  }
}

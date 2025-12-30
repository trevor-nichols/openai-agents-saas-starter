import { chromium, type BrowserContext } from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';

import { ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE, SESSION_META_COOKIE } from '../../lib/config';

export type StorageStateRole = 'tenant-admin' | 'operator';
export type StorageStateMode = 'real' | 'mock';

const isLocalUrl = (url: string) => url.startsWith('http://localhost') || url.startsWith('http://127.0.0.1');

export function getStorageStatePath(role: StorageStateRole, mode: StorageStateMode = 'real'): string {
  return path.resolve(__dirname, '..', '.auth', `${mode}-${role}.json`);
}

async function fileExists(filePath: string): Promise<boolean> {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function isStorageStateFresh(storagePath: string): Promise<boolean> {
  try {
    const raw = await fs.readFile(storagePath, 'utf8');
    const state = JSON.parse(raw) as { cookies?: Array<{ name?: string; expires?: number }> };
    const accessCookie = state.cookies?.find((cookie) => cookie.name === ACCESS_TOKEN_COOKIE);
    if (!accessCookie?.expires) {
      return false;
    }
    const expiresMs = accessCookie.expires * 1000;
    return expiresMs - Date.now() > 60_000;
  } catch {
    return false;
  }
}

async function loginAndSaveState(options: {
  baseURL: string;
  storagePath: string;
  email: string;
  password: string;
}): Promise<void> {
  const browser = await chromium.launch();
  const context = await browser.newContext({ baseURL: options.baseURL });
  try {
    const apiLoggedIn = await tryApiLogin(context, options);

    if (!apiLoggedIn) {
      const page = await context.newPage();
      await page.goto('/login');
      await page.getByLabel('Email').fill(options.email);
      await page.getByLabel('Password').fill(options.password);
      await Promise.all([
        page.waitForURL(/\/dashboard$/, { waitUntil: 'domcontentloaded' }),
        page.getByRole('button', { name: /sign in/i }).click(),
      ]);
    }

    await fs.mkdir(path.dirname(options.storagePath), { recursive: true });
    await context.storageState({ path: options.storagePath });
  } finally {
    await context.close();
    await browser.close();
  }
}

async function tryApiLogin(
  context: BrowserContext,
  options: { baseURL: string; email: string; password: string },
): Promise<boolean> {
  const response = await context.request.post('/api/v1/auth/token', {
    data: {
      email: options.email,
      password: options.password,
    },
  });

  if (!response.ok()) {
    return false;
  }

  const payload = (await response.json()) as {
    access_token: string;
    refresh_token: string;
    expires_at: string;
    refresh_expires_at: string;
    tenant_id: string;
    user_id: string;
    scopes: string[];
  };

  const baseUrl = new URL(options.baseURL);
  const domain = baseUrl.hostname;
  const secure = baseUrl.protocol === 'https:';
  const accessExpires = Math.floor(new Date(payload.expires_at).getTime() / 1000);
  const refreshExpires = Math.floor(new Date(payload.refresh_expires_at).getTime() / 1000);
  const metaPayload = Buffer.from(
    JSON.stringify({
      expiresAt: payload.expires_at,
      refreshExpiresAt: payload.refresh_expires_at,
      userId: payload.user_id,
      tenantId: payload.tenant_id,
      scopes: payload.scopes,
    }),
  ).toString('base64url');

  await context.addCookies([
    {
      name: ACCESS_TOKEN_COOKIE,
      value: payload.access_token,
      domain,
      path: '/',
      expires: accessExpires,
      httpOnly: true,
      secure,
      sameSite: 'Lax',
    },
    {
      name: REFRESH_TOKEN_COOKIE,
      value: payload.refresh_token,
      domain,
      path: '/',
      expires: refreshExpires,
      httpOnly: true,
      secure,
      sameSite: 'Strict',
    },
    {
      name: SESSION_META_COOKIE,
      value: metaPayload,
      domain,
      path: '/',
      expires: refreshExpires,
      httpOnly: false,
      secure,
      sameSite: 'Lax',
    },
  ]);

  return true;
}

export async function ensureStorageState(options: {
  baseURL: string | undefined;
  storagePath: string;
  email: string;
  password: string;
  refresh: boolean;
  skip: boolean;
}): Promise<void> {
  if (options.skip || !options.baseURL) {
    return;
  }

  const storageExists = await fileExists(options.storagePath);
  if (storageExists && !options.refresh) {
    const isFresh = await isStorageStateFresh(options.storagePath);
    if (isFresh) {
      return;
    }
  }

  const isRemote = !isLocalUrl(options.baseURL);
  if (isRemote && !storageExists && !options.refresh) {
    console.warn(
      `Skipping storage state generation for ${options.baseURL}. Provide ${options.storagePath} or set PLAYWRIGHT_REFRESH_STORAGE_STATE=true to log in remotely.`,
    );
    return;
  }

  await loginAndSaveState({
    baseURL: options.baseURL,
    storagePath: options.storagePath,
    email: options.email,
    password: options.password,
  });
}

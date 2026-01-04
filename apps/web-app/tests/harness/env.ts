import { z } from 'zod';

const truthy = new Set(['1', 'true', 'yes', 'on']);

const EnvSchema = z.object({
  PLAYWRIGHT_BASE_URL: z.string().url(),
  PLAYWRIGHT_MOCK_BASE_URL: z.string().url(),
  PLAYWRIGHT_API_URL: z.string().url(),
  PLAYWRIGHT_TENANT_ADMIN_EMAIL: z.string().email(),
  PLAYWRIGHT_TENANT_ADMIN_PASSWORD: z.string().min(1),
  PLAYWRIGHT_OPERATOR_EMAIL: z.string().email(),
  PLAYWRIGHT_OPERATOR_PASSWORD: z.string().min(1),
  PLAYWRIGHT_TENANT_SLUG: z.string().min(1),
  PLAYWRIGHT_OPERATOR_TENANT: z.string().min(1),
  PLAYWRIGHT_BILLING_EMAIL: z.string().email().optional(),
  PLAYWRIGHT_SKIP_WEB_SERVER: z.string().optional(),
  PLAYWRIGHT_SEED_ON_START: z.string().optional(),
  PLAYWRIGHT_SKIP_SEED: z.string().optional(),
  PLAYWRIGHT_REFRESH_STORAGE_STATE: z.string().optional(),
  PLAYWRIGHT_SKIP_STORAGE_STATE: z.string().optional(),
  SIGNUP_ACCESS_POLICY: z.string().optional(),
  CI: z.string().optional(),
});

type RawEnv = z.infer<typeof EnvSchema>;

export interface PlaywrightEnv {
  baseUrl: string;
  mockBaseUrl: string;
  apiBaseUrl: string;
  tenantAdmin: {
    email: string;
    password: string;
  };
  operator: {
    email: string;
    password: string;
  };
  tenantSlugs: {
    primary: string;
    operator: string;
  };
  billingEmail: string;
  flags: {
    isCI: boolean;
    skipWebServer: boolean;
    seedOnStart: boolean;
    skipSeed: boolean;
    refreshStorageState: boolean;
    skipStorageState: boolean;
    allowPublicSignup: boolean;
  };
}

let cachedEnv: PlaywrightEnv | null = null;

function normalizeUrl(value: string): string {
  return value.replace(/\/+$/, '');
}

function isTruthy(value: string | undefined): boolean {
  if (!value) return false;
  return truthy.has(value.trim().toLowerCase());
}

function buildRawEnv(): RawEnv {
  return EnvSchema.parse({
    PLAYWRIGHT_BASE_URL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000',
    PLAYWRIGHT_MOCK_BASE_URL: process.env.PLAYWRIGHT_MOCK_BASE_URL ?? 'http://localhost:3001',
    PLAYWRIGHT_API_URL:
      process.env.PLAYWRIGHT_API_URL ??
      process.env.API_BASE_URL ??
      'http://localhost:8000',
    PLAYWRIGHT_TENANT_ADMIN_EMAIL: process.env.PLAYWRIGHT_TENANT_ADMIN_EMAIL ?? 'user@example.com',
    PLAYWRIGHT_TENANT_ADMIN_PASSWORD: process.env.PLAYWRIGHT_TENANT_ADMIN_PASSWORD ?? 'SuperSecret123!',
    PLAYWRIGHT_OPERATOR_EMAIL: process.env.PLAYWRIGHT_OPERATOR_EMAIL ?? 'platform-ops@example.com',
    PLAYWRIGHT_OPERATOR_PASSWORD: process.env.PLAYWRIGHT_OPERATOR_PASSWORD ?? 'OpsAccount123!',
    PLAYWRIGHT_TENANT_SLUG: process.env.PLAYWRIGHT_TENANT_SLUG ?? 'playwright-starter',
    PLAYWRIGHT_OPERATOR_TENANT: process.env.PLAYWRIGHT_OPERATOR_TENANT ?? 'platform-ops',
    PLAYWRIGHT_BILLING_EMAIL: process.env.PLAYWRIGHT_BILLING_EMAIL,
    SIGNUP_ACCESS_POLICY: process.env.SIGNUP_ACCESS_POLICY,
    PLAYWRIGHT_SKIP_WEB_SERVER: process.env.PLAYWRIGHT_SKIP_WEB_SERVER,
    PLAYWRIGHT_SEED_ON_START: process.env.PLAYWRIGHT_SEED_ON_START,
    PLAYWRIGHT_SKIP_SEED: process.env.PLAYWRIGHT_SKIP_SEED,
    PLAYWRIGHT_REFRESH_STORAGE_STATE: process.env.PLAYWRIGHT_REFRESH_STORAGE_STATE,
    PLAYWRIGHT_SKIP_STORAGE_STATE: process.env.PLAYWRIGHT_SKIP_STORAGE_STATE,
    CI: process.env.CI,
  });
}

export function getPlaywrightEnv(): PlaywrightEnv {
  if (cachedEnv) return cachedEnv;

  const raw = buildRawEnv();
  const apiBaseUrl = normalizeUrl(raw.PLAYWRIGHT_API_URL);
  const baseUrl = normalizeUrl(raw.PLAYWRIGHT_BASE_URL);
  const mockBaseUrl = normalizeUrl(raw.PLAYWRIGHT_MOCK_BASE_URL);

  cachedEnv = {
    baseUrl,
    mockBaseUrl,
    apiBaseUrl,
    tenantAdmin: {
      email: raw.PLAYWRIGHT_TENANT_ADMIN_EMAIL,
      password: raw.PLAYWRIGHT_TENANT_ADMIN_PASSWORD,
    },
    operator: {
      email: raw.PLAYWRIGHT_OPERATOR_EMAIL,
      password: raw.PLAYWRIGHT_OPERATOR_PASSWORD,
    },
    tenantSlugs: {
      primary: raw.PLAYWRIGHT_TENANT_SLUG,
      operator: raw.PLAYWRIGHT_OPERATOR_TENANT,
    },
    billingEmail: raw.PLAYWRIGHT_BILLING_EMAIL ?? 'billing+playwright@example.com',
    flags: {
      isCI: isTruthy(raw.CI),
      skipWebServer: isTruthy(raw.PLAYWRIGHT_SKIP_WEB_SERVER),
      seedOnStart: isTruthy(raw.PLAYWRIGHT_SEED_ON_START),
      skipSeed: isTruthy(raw.PLAYWRIGHT_SKIP_SEED),
      refreshStorageState: isTruthy(raw.PLAYWRIGHT_REFRESH_STORAGE_STATE),
      skipStorageState: isTruthy(raw.PLAYWRIGHT_SKIP_STORAGE_STATE),
      allowPublicSignup: raw.SIGNUP_ACCESS_POLICY?.trim().toLowerCase() === 'public',
    },
  };

  return cachedEnv;
}

export function getApiBaseUrl(): string {
  return getPlaywrightEnv().apiBaseUrl;
}

export function isPublicSignupEnabled(): boolean {
  return getPlaywrightEnv().flags.allowPublicSignup;
}

export function resetPlaywrightEnvCache(): void {
  cachedEnv = null;
}

export type { RawEnv };

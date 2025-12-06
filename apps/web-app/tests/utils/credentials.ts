export interface LoginCredentials {
  email: string;
  password: string;
}

function getEnv(name: string): string | undefined {
  const value = process.env[name];
  if (value && value.trim()) {
    return value.trim();
  }
  return undefined;
}

function buildCredentials(envEmailKey: string, envPasswordKey: string, defaults: LoginCredentials): LoginCredentials {
  const email = getEnv(envEmailKey) ?? defaults.email;
  const password = getEnv(envPasswordKey) ?? defaults.password;
  if (!email || !password) {
    throw new Error(`Missing credentials for ${envEmailKey}/${envPasswordKey}. Set env vars or update seeds.`);
  }
  return { email, password };
}

export function getTenantAdminCredentials(): LoginCredentials {
  return buildCredentials(
    'PLAYWRIGHT_TENANT_ADMIN_EMAIL',
    'PLAYWRIGHT_TENANT_ADMIN_PASSWORD',
    {
      email: 'user@example.com',
      password: 'SuperSecret123!',
    },
  );
}

export function getOperatorCredentials(): LoginCredentials {
  return buildCredentials(
    'PLAYWRIGHT_OPERATOR_EMAIL',
    'PLAYWRIGHT_OPERATOR_PASSWORD',
    {
      email: 'platform-ops@example.com',
      password: 'OpsAccount123!',
    },
  );
}

export function getPrimaryTenantSlug(): string {
  return getEnv('PLAYWRIGHT_TENANT_SLUG') ?? 'playwright-starter';
}

export function getOperatorTenantSlug(): string {
  return getEnv('PLAYWRIGHT_OPERATOR_TENANT') ?? 'platform-ops';
}

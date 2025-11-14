import type {
  ServiceAccountIssueMode,
  ServiceAccountIssuePayload,
} from '@/types/serviceAccounts';

export type ServiceAccountIssueFormValues = {
  account: string;
  scopes: string;
  tenantId: string | null;
  lifetimeMinutes?: number | null;
  fingerprint?: string;
  force?: boolean;
  reason: string;
  mode: ServiceAccountIssueMode;
  vaultAuthorization?: string;
  vaultPayload?: string;
};

export function createDefaultIssueForm(tenantId: string | null = null): ServiceAccountIssueFormValues {
  return {
    account: '',
    scopes: '',
    tenantId,
    lifetimeMinutes: undefined,
    fingerprint: undefined,
    force: false,
    reason: '',
    mode: 'browser',
    vaultAuthorization: '',
    vaultPayload: '',
  };
}

export function buildIssuePayload(
  form: ServiceAccountIssueFormValues,
  fallbackTenantId: string | null,
): ServiceAccountIssuePayload {
  const account = form.account.trim();
  if (!account) {
    throw new Error('Account is required.');
  }

  const scopes = parseScopesInput(form.scopes);
  if (scopes.length === 0) {
    throw new Error('Add at least one scope.');
  }

  const reason = form.reason.trim();
  if (reason.length < 10) {
    throw new Error('Reason must be at least 10 characters.');
  }

  let lifetimeMinutes: number | null | undefined = form.lifetimeMinutes;
  if (typeof lifetimeMinutes === 'string') {
    lifetimeMinutes = lifetimeMinutes ? Number(lifetimeMinutes) : undefined;
  }
  if (typeof lifetimeMinutes === 'number') {
    if (Number.isNaN(lifetimeMinutes) || lifetimeMinutes <= 0) {
      throw new Error('Lifetime must be a positive number.');
    }
  }

  const tenantId = form.tenantId ?? fallbackTenantId ?? null;

  const base = {
    account,
    scopes,
    tenantId,
    lifetimeMinutes: lifetimeMinutes ?? undefined,
    fingerprint: sanitizeOptionalString(form.fingerprint),
    force: Boolean(form.force),
    reason,
  };

  if (form.mode === 'vault') {
    const authorization = sanitizeOptionalString(form.vaultAuthorization);
    if (!authorization) {
      throw new Error('Provide the Vault Authorization header value.');
    }

    return {
      ...base,
      mode: 'vault',
      vaultAuthorization: authorization,
      vaultPayload: sanitizeOptionalString(form.vaultPayload),
    };
  }

  return {
    ...base,
    mode: 'browser',
  };
}

export function parseScopesInput(value: string): string[] {
  return value
    .split(/[,\n]/)
    .map((scope) => scope.trim())
    .filter((scope) => scope.length > 0);
}

function sanitizeOptionalString(value?: string | null): string | undefined {
  if (!value) return undefined;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

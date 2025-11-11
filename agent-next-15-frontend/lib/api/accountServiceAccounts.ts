import type {
  ServiceAccountIssuePayload,
  ServiceAccountIssueResult,
  ServiceAccountTokenListResult,
  ServiceAccountTokenQueryParams,
} from '@/types/serviceAccounts';

interface TokensApiResponse {
  success: boolean;
  tokens?: ServiceAccountTokenListResult['tokens'];
  total?: number;
  limit?: number;
  offset?: number;
  error?: string;
}

interface RevokeApiResponse {
  success: boolean;
  data?: {
    jti: string;
  };
  error?: string;
}

interface IssueApiResponse {
  success: boolean;
  data?: ServiceAccountIssueResult;
  error?: string;
}

export type { ServiceAccountTokenQueryParams };

export async function fetchServiceAccountTokens(
  params: ServiceAccountTokenQueryParams = {},
): Promise<ServiceAccountTokenListResult> {
  const search = new URLSearchParams();
  if (params.account) {
    search.set('account', params.account);
  }
  if (params.fingerprint) {
    search.set('fingerprint', params.fingerprint);
  }
  if (params.status) {
    search.set('status', params.status);
  }
  if (typeof params.limit === 'number') {
    search.set('limit', String(params.limit));
  }
  if (typeof params.offset === 'number') {
    search.set('offset', String(params.offset));
  }
  if (params.tenantId) {
    search.set('tenant_id', params.tenantId);
  }
  if (typeof params.includeGlobal === 'boolean') {
    search.set('include_global', String(params.includeGlobal));
  }

  const qs = search.toString();
  const response = await fetch(`/api/auth/service-accounts/tokens${qs ? `?${qs}` : ''}`, {
    method: 'GET',
    cache: 'no-store',
  });

  const payload = (await response.json()) as TokensApiResponse;

  if (!response.ok || payload.success === false || !payload.tokens) {
    throw new Error(payload.error || 'Failed to load service-account tokens.');
  }

  return {
    tokens: payload.tokens,
    total: payload.total ?? payload.tokens.length,
    limit: payload.limit ?? params.limit ?? payload.tokens.length,
    offset: payload.offset ?? params.offset ?? 0,
  };
}

export async function revokeServiceAccountTokenRequest(
  tokenId: string,
  reason?: string,
): Promise<void> {
  if (!tokenId) {
    throw new Error('Token id is required.');
  }

  const body = reason && reason.trim().length > 0 ? { reason: reason.trim() } : {};

  const response = await fetch(
    `/api/auth/service-accounts/tokens/${encodeURIComponent(tokenId)}/revoke`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      cache: 'no-store',
    },
  );

  const payload = (await response.json().catch(() => ({}))) as RevokeApiResponse;

  if (!response.ok || payload.success === false) {
    throw new Error(payload.error || 'Failed to revoke service-account token.');
  }
}

export async function issueServiceAccountTokenRequest(
  payload: ServiceAccountIssuePayload,
): Promise<ServiceAccountIssueResult> {
  const response = await fetch('/api/auth/service-accounts/browser-issue', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      account: payload.account,
      scopes: payload.scopes,
      tenant_id: payload.tenantId,
      lifetime_minutes: payload.lifetimeMinutes,
      fingerprint: payload.fingerprint,
      force: payload.force ?? false,
      reason: payload.reason,
    }),
    cache: 'no-store',
  });

  const result = (await response.json().catch(() => ({}))) as IssueApiResponse;
  if (!response.ok || result.success === false || !result.data) {
    throw new Error(result.error || 'Failed to issue service-account token.');
  }

  return result.data;
}

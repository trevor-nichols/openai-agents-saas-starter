'use server';

import {
  issueServiceAccountTokenApiV1AuthServiceAccountsIssuePost,
  listServiceAccountTokensApiV1AuthServiceAccountsTokensGet,
  revokeServiceAccountTokenApiV1AuthServiceAccountsTokensJtiRevokePost,
} from '@/lib/api/client/sdk.gen';
import type {
  ServiceAccountTokenResponse,
  ServiceAccountTokenItem,
  ServiceAccountTokenRevokeRequest,
  ServiceAccountTokenRevokeSuccessResponse,
} from '@/lib/api/client/types.gen';
import type {
  BrowserServiceAccountIssuePayload,
  ServiceAccountIssueResult,
  ServiceAccountTokenListResult,
  ServiceAccountTokenQueryParams,
  ServiceAccountTokenSummary,
  VaultServiceAccountIssuePayload,
} from '@/types/serviceAccounts';
import { API_BASE_URL } from '@/lib/config';

import { getServerApiClient } from '../../apiClient';

const DEFAULT_LIMIT = 50;
const MAX_LIMIT = 100;

export async function listServiceAccountTokens(
  params: ServiceAccountTokenQueryParams = {},
): Promise<ServiceAccountTokenListResult> {
  const { client, auth } = await getServerApiClient();

  const limit = clampLimit(params.limit);
  const offset = clampOffset(params.offset);

  const response = await listServiceAccountTokensApiV1AuthServiceAccountsTokensGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    query: {
      account: params.account ?? undefined,
      fingerprint: params.fingerprint ?? undefined,
      status: params.status ?? 'active',
      tenant_id: params.tenantId ?? undefined,
      include_global: params.includeGlobal ?? undefined,
      limit,
      offset,
    },
  });

  const payload = response.data;

  if (!payload) {
    throw new Error('Service-account token list returned no data.');
  }

  return {
    tokens: payload.items?.map(mapTokenItem) ?? [],
    total: payload.total ?? 0,
    limit: payload.limit ?? limit,
    offset: payload.offset ?? offset,
  };
}

export async function revokeServiceAccountToken(
  tokenId: string,
  reason?: string | null,
): Promise<ServiceAccountTokenRevokeSuccessResponse> {
  if (!tokenId) {
    throw new Error('Token id is required.');
  }

  const { client, auth } = await getServerApiClient();

  const payload: ServiceAccountTokenRevokeRequest = {
    reason: reason ?? undefined,
  };

  const response = await revokeServiceAccountTokenApiV1AuthServiceAccountsTokensJtiRevokePost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      'Content-Type': 'application/json',
    },
    path: {
      jti: tokenId,
    },
    body: payload,
  });

  if (!response.data) {
    throw new Error('Failed to revoke service-account token.');
  }

  return response.data;
}

export async function issueServiceAccountToken(
  payload: BrowserServiceAccountIssuePayload,
): Promise<ServiceAccountIssueResult> {
  const { auth } = await getServerApiClient();
  const token = auth();
  const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;

  const response = await fetch(`${baseUrl}/api/v1/auth/service-accounts/browser-issue`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      account: payload.account,
      scopes: payload.scopes,
      tenant_id: payload.tenantId ?? undefined,
      lifetime_minutes: payload.lifetimeMinutes,
      fingerprint: payload.fingerprint,
      force: payload.force ?? false,
      reason: payload.reason,
    }),
  });

  const data = (await response.json().catch(() => ({}))) as Record<string, unknown>;

  if (!response.ok || !data) {
    const message =
      typeof data?.detail === 'string'
        ? data.detail
        : typeof data?.message === 'string'
          ? data.message
          : typeof data?.error === 'string'
            ? data.error
            : 'Failed to issue service-account token.';
    throw new Error(message);
  }

  return mapServiceAccountResponse(data, payload);
}

export async function issueVaultServiceAccountToken(
  payload: VaultServiceAccountIssuePayload,
): Promise<ServiceAccountIssueResult> {
  if (!payload.vaultAuthorization) {
    throw new Error('Vault authorization header is required.');
  }

  const { client } = await getServerApiClient();

  const response = await issueServiceAccountTokenApiV1AuthServiceAccountsIssuePost({
    client,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      Authorization: payload.vaultAuthorization,
      'X-Vault-Payload': payload.vaultPayload ?? undefined,
    },
    body: {
      account: payload.account,
      scopes: payload.scopes,
      tenant_id: payload.tenantId ?? undefined,
      lifetime_minutes: payload.lifetimeMinutes ?? undefined,
      fingerprint: payload.fingerprint ?? undefined,
      force: payload.force ?? false,
    },
  });

  if (!response.data) {
    throw new Error('Service-account issue endpoint returned no data.');
  }

  return mapServiceAccountResponse(response.data, payload);
}

function mapTokenItem(item: ServiceAccountTokenItem): ServiceAccountTokenSummary {
  return {
    id: item.jti,
    account: item.account,
    tenantId: item.tenant_id ?? null,
    scopes: item.scopes ?? [],
    issuedAt: item.issued_at,
    expiresAt: item.expires_at,
    revokedAt: item.revoked_at ?? null,
    revokedReason: item.revoked_reason ?? null,
    fingerprint: item.fingerprint ?? null,
    signingKeyId: item.signing_kid,
  };
}

function clampLimit(value?: number | null): number {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return DEFAULT_LIMIT;
  }
  return Math.min(Math.max(1, Math.trunc(value)), MAX_LIMIT);
}

function clampOffset(value?: number | null): number {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 0;
  }
  return Math.max(0, Math.trunc(value));
}

function mapServiceAccountResponse(
  data: Record<string, unknown> | Partial<ServiceAccountTokenResponse>,
  fallback: {
    account: string;
    tenantId: string | null;
    scopes: string[];
  },
): ServiceAccountIssueResult {
  const refreshToken = typeof data.refresh_token === 'string' ? data.refresh_token : '';
  if (!refreshToken) {
    throw new Error('Server did not return a refresh token.');
  }

  const expiresAt = typeof data.expires_at === 'string' ? data.expires_at : '';
  const issuedAt = typeof data.issued_at === 'string' ? data.issued_at : '';
  const kid = typeof data.kid === 'string' ? data.kid : 'unknown';
  const account = typeof data.account === 'string' ? data.account : fallback.account;
  const tokenUse = typeof data.token_use === 'string' ? data.token_use : 'refresh';
  const tenantId =
    typeof data.tenant_id === 'string' || data.tenant_id === null
      ? (data.tenant_id as string | null)
      : fallback.tenantId;
  const scopes = Array.isArray(data.scopes) ? (data.scopes as string[]) : fallback.scopes;

  return {
    refreshToken,
    account,
    tenantId,
    scopes,
    expiresAt,
    issuedAt,
    kid,
    tokenUse,
  };
}

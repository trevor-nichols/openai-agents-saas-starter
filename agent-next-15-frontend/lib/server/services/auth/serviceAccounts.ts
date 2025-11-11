'use server';

import {
  listServiceAccountTokensApiV1AuthServiceAccountsTokensGet,
  revokeServiceAccountTokenApiV1AuthServiceAccountsTokensJtiRevokePost,
} from '@/lib/api/client/sdk.gen';
import type {
  ServiceAccountTokenItem,
  ServiceAccountTokenRevokeRequest,
  SuccessResponse,
} from '@/lib/api/client/types.gen';
import type {
  ServiceAccountTokenListResult,
  ServiceAccountTokenQueryParams,
  ServiceAccountTokenSummary,
} from '@/types/serviceAccounts';

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
): Promise<SuccessResponse> {
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

import 'server-only';

import {
  completeSsoApiV1AuthSsoProviderCallbackPost,
  listSsoProvidersApiV1AuthSsoProvidersGet,
  startSsoApiV1AuthSsoProviderStartPost,
} from '@/lib/api/client/sdk.gen';
import type {
  MfaChallengeResponse,
  SsoCallbackRequest,
  SsoProviderListResponse,
  SsoStartRequest,
  SsoStartResponse,
  UserSessionResponse,
} from '@/lib/api/client/types.gen';
import { createApiClient } from '../../apiClient';

export async function listSsoProviders(params: {
  tenantId?: string | null;
  tenantSlug?: string | null;
}): Promise<SsoProviderListResponse> {
  const client = createApiClient();
  const response = await listSsoProvidersApiV1AuthSsoProvidersGet({
    client,
    responseStyle: 'fields',
    throwOnError: true,
    query: {
      tenant_id: params.tenantId ?? undefined,
      tenant_slug: params.tenantSlug ?? undefined,
    },
  });

  return response.data ?? { providers: [] };
}

export async function startSso(
  provider: string,
  payload: SsoStartRequest,
): Promise<{ data?: SsoStartResponse; status: number }> {
  const client = createApiClient();
  const response = await startSsoApiV1AuthSsoProviderStartPost({
    client,
    responseStyle: 'fields',
    throwOnError: true,
    path: { provider },
    body: payload,
  });

  return {
    data: response.data ?? undefined,
    status: response.response?.status ?? 200,
  };
}

export async function completeSso(
  provider: string,
  payload: SsoCallbackRequest,
): Promise<{ data?: UserSessionResponse | MfaChallengeResponse; status: number }> {
  const client = createApiClient();
  const response = await completeSsoApiV1AuthSsoProviderCallbackPost({
    client,
    responseStyle: 'fields',
    throwOnError: true,
    path: { provider },
    body: payload,
  });

  return {
    data: response.data ?? undefined,
    status: response.response?.status ?? 200,
  };
}

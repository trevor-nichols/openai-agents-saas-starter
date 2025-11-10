'use server';

import { issueServiceAccountTokenApiV1AuthServiceAccountsIssuePost } from '@/lib/api/client/sdk.gen';
import type {
  ServiceAccountIssueRequest,
  ServiceAccountTokenResponse,
} from '@/lib/api/client/types.gen';

import { getServerApiClient } from '../../apiClient';

export async function issueServiceAccountToken(
  payload: ServiceAccountIssueRequest,
  options?: { vaultPayload?: string | null },
): Promise<ServiceAccountTokenResponse> {
  const { client, auth } = await getServerApiClient();

  const authorization = auth();
  const response = await issueServiceAccountTokenApiV1AuthServiceAccountsIssuePost({
    client,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      Authorization: authorization,
      ...(options?.vaultPayload ? { 'X-Vault-Payload': options.vaultPayload } : {}),
    },
    body: payload,
  });

  const data = response.data;
  if (!data) {
    throw new Error('Service account issuance returned empty response.');
  }

  return data;
}


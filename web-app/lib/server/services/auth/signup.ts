'use server';

import { registerTenantApiV1AuthRegisterPost } from '@/lib/api/client/sdk.gen';
import type { UserRegisterRequest, UserRegisterResponse } from '@/lib/api/client/types.gen';

import { createApiClient } from '../../apiClient';

export async function registerTenant(payload: UserRegisterRequest): Promise<UserRegisterResponse> {
  const response = await registerTenantApiV1AuthRegisterPost({
    client: createApiClient(),
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      'Content-Type': 'application/json',
    },
    body: payload,
  });

  const data = response.data;
  if (!data) {
    throw new Error('Registration returned empty response.');
  }

  return data;
}


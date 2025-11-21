'use server';

import { redirect } from 'next/navigation';

import { registerTenant } from '@/lib/server/services/auth/signup';
import type { UserRegisterRequest } from '@/lib/api/client/types.gen';
import { persistSessionCookies } from '@/lib/auth/cookies';

export async function registerTenantAction(
  payload: UserRegisterRequest,
  options?: { redirectTo?: string },
) {
  const response = await registerTenant(payload);
  await persistSessionCookies({
    access_token: response.access_token,
    refresh_token: response.refresh_token,
    token_type: response.token_type ?? 'bearer',
    expires_at: response.expires_at,
    refresh_expires_at: response.refresh_expires_at,
    kid: response.kid,
    refresh_kid: response.refresh_kid,
    scopes: response.scopes,
    tenant_id: response.tenant_id,
    user_id: response.user_id,
  });

  if (options?.redirectTo) {
    redirect(options.redirectTo);
  }

  return response;
}


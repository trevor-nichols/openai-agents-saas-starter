'use server';

import { redirect } from 'next/navigation';

import { persistSessionCookies } from '@/lib/auth/cookies';
import { acceptTeamInvite } from '@/lib/server/services/team';
import type { TeamInviteAcceptInput } from '@/types/team';

export async function acceptTeamInviteAction(
  payload: TeamInviteAcceptInput,
  options?: { redirectTo?: string },
) {
  const response = await acceptTeamInvite(payload);
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

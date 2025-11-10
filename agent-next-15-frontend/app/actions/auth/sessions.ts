'use server';

import { redirect } from 'next/navigation';

import {
  listUserSessions,
  logoutAllSessions,
  logoutSession,
  revokeUserSession,
} from '@/lib/server/services/auth/sessions';
import type { SessionListParams } from '@/lib/server/services/auth/sessions';
import type { UserLogoutRequest } from '@/lib/api/client/types.gen';
import { destroySession } from '@/lib/auth/session';

export async function listSessionsAction(params?: SessionListParams) {
  return listUserSessions(params);
}

export async function logoutSessionAction(payload: UserLogoutRequest, { redirectTo }: { redirectTo?: string } = {}) {
  await logoutSession(payload);
  await destroySession();
  if (redirectTo) {
    redirect(redirectTo);
  }
}

export async function logoutAllSessionsAction({ redirectTo }: { redirectTo?: string } = {}) {
  await logoutAllSessions();
  await destroySession();
  if (redirectTo) {
    redirect(redirectTo);
  }
}

export async function revokeSessionAction(sessionId: string) {
  return revokeUserSession(sessionId);
}


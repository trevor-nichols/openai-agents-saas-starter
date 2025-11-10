/**
 * API Layer - Session management
 */

import type { SessionResponse } from '@/types/session';

/**
 * Fetch current session info
 */
export async function fetchSession(): Promise<SessionResponse> {
  const response = await fetch('/api/auth/session', { cache: 'no-store' });

  if (!response.ok) {
    throw new Error(`Session check failed: ${response.status}`);
  }

  return response.json() as Promise<SessionResponse>;
}

/**
 * Refresh the current session (extends expiration)
 */
export async function refreshSession(): Promise<SessionResponse> {
  const response = await fetch('/api/auth/refresh', { method: 'POST' });

  if (!response.ok) {
    throw new Error(`Session refresh failed: ${response.status}`);
  }

  return response.json() as Promise<SessionResponse>;
}

/**
 * Redirect to login page
 */
export function redirectToLogin(): void {
  window.location.href = '/login';
}

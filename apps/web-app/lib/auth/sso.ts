import type { MfaChallengeResponse, UserSessionResponse } from '@/lib/api/client/types.gen';

const TENANT_UUID_REGEX =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export type TenantSelector =
  | { tenant_id: string; tenant_slug?: never }
  | { tenant_slug: string; tenant_id?: never };

export function resolveTenantSelector(value?: string | null): TenantSelector | null {
  const trimmed = value?.trim();
  if (!trimmed) {
    return null;
  }
  if (TENANT_UUID_REGEX.test(trimmed)) {
    return { tenant_id: trimmed };
  }
  return { tenant_slug: trimmed };
}

export function resolveSafeRedirect(value?: string | null): string | null {
  const trimmed = value?.trim();
  if (!trimmed) {
    return null;
  }
  if (!trimmed.startsWith('/') || trimmed.startsWith('//')) {
    return null;
  }
  return trimmed;
}

export function isMfaChallengeResponse(payload: unknown): payload is MfaChallengeResponse {
  return Boolean(payload && typeof payload === 'object' && 'challenge_token' in payload);
}

export function isUserSessionResponse(payload: unknown): payload is UserSessionResponse {
  return Boolean(payload && typeof payload === 'object' && 'access_token' in payload);
}

import type { MfaChallengeResponse, UserSessionResponse } from '@/lib/api/client/types.gen';

export type TenantSelector =
  | { tenant_id: string; tenant_slug?: never }
  | { tenant_slug: string; tenant_id?: never };

export type TenantSelectionInput = {
  tenantId?: string | null;
  tenantSlug?: string | null;
};

export type TenantSelectionResult = {
  selector: TenantSelector | null;
  conflict: boolean;
};

export function resolveTenantSelection({
  tenantId,
  tenantSlug,
}: TenantSelectionInput): TenantSelectionResult {
  const normalizedTenantId = tenantId?.trim();
  const normalizedTenantSlug = tenantSlug?.trim();
  const conflict = Boolean(normalizedTenantId && normalizedTenantSlug);

  if (conflict) {
    return { selector: null, conflict };
  }

  if (normalizedTenantId) {
    return { selector: { tenant_id: normalizedTenantId }, conflict: false };
  }

  if (normalizedTenantSlug) {
    return { selector: { tenant_slug: normalizedTenantSlug }, conflict: false };
  }

  return { selector: null, conflict: false };
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

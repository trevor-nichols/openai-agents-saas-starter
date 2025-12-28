import type { NextRequest } from 'next/server';

export interface BillingTenantRouteContext {
  params: Promise<{
    tenantId?: string;
  }>;
}

export async function resolveTenantId(context: BillingTenantRouteContext): Promise<string | null> {
  const { tenantId } = await context.params;
  return tenantId ?? null;
}

export function resolveTenantRole(request: NextRequest): string | null {
  return request.headers.get('x-tenant-role');
}

export function mapBillingErrorToStatus(
  message: string,
  options?: { includeNotFound?: boolean },
): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  if (options?.includeNotFound && normalized.includes('not found')) {
    return 404;
  }
  return 400;
}

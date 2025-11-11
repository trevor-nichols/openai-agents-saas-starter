import { NextRequest, NextResponse } from 'next/server';

import { listServiceAccountTokens } from '@/lib/server/services/auth/serviceAccounts';
import type { ServiceAccountStatusFilter } from '@/types/serviceAccounts';

const VALID_STATUS: ReadonlySet<ServiceAccountStatusFilter> = new Set(['active', 'revoked', 'all']);

export async function GET(request: NextRequest) {
  const url = new URL(request.url);

  const account = normalizeQueryValue(url.searchParams.get('account'));
  const fingerprint = normalizeQueryValue(url.searchParams.get('fingerprint'));
  const status = parseStatus(url.searchParams.get('status'));
  const limit = parseNumber(url.searchParams.get('limit'));
  const offset = parseNumber(url.searchParams.get('offset'));
  const tenantId = normalizeQueryValue(url.searchParams.get('tenant_id'));
  const includeGlobal = parseBoolean(url.searchParams.get('include_global'));

  try {
    const result = await listServiceAccountTokens({
      account,
      fingerprint,
      status,
      tenantId,
      includeGlobal,
      limit,
      offset,
    });

    return NextResponse.json(
      {
        success: true,
        tokens: result.tokens,
        total: result.total,
        limit: result.limit,
        offset: result.offset,
      },
      { status: 200 },
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load service-account tokens.';
    const statusCode = mapErrorToStatus(message);
    return NextResponse.json(
      {
        success: false,
        error: message,
      },
      { status: statusCode },
    );
  }
}

function normalizeQueryValue(value: string | null): string | undefined {
  if (!value) {
    return undefined;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

function parseStatus(value: string | null): ServiceAccountStatusFilter | undefined {
  if (!value) {
    return undefined;
  }
  if (VALID_STATUS.has(value as ServiceAccountStatusFilter)) {
    return value as ServiceAccountStatusFilter;
  }
  return undefined;
}

function parseNumber(value: string | null): number | undefined {
  if (!value) {
    return undefined;
  }
  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) ? undefined : parsed;
}

function parseBoolean(value: string | null): boolean | undefined {
  if (value === null) {
    return undefined;
  }
  if (value.toLowerCase() === 'true') {
    return true;
  }
  if (value.toLowerCase() === 'false') {
    return false;
  }
  return undefined;
}

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  if (normalized.includes('forbidden')) {
    return 403;
  }
  return 500;
}

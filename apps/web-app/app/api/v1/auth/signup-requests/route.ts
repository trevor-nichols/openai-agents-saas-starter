import { NextRequest, NextResponse } from 'next/server';

import { normalizeSignupGuardrailError } from '@/app/api/v1/auth/_utils/signupGuardrailResponses';
import { listSignupRequests } from '@/lib/server/services/auth/signupGuardrails';
import type { SignupRequestStatusFilter } from '@/types/signup';

const VALID_STATUSES: ReadonlySet<SignupRequestStatusFilter> = new Set([
  'pending',
  'approved',
  'rejected',
]);

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const filters = {
    status: parseStatus(url.searchParams.get('status')),
    limit: parseNumber(url.searchParams.get('limit')),
    offset: parseNumber(url.searchParams.get('offset')),
  };

  try {
    const result = await listSignupRequests(filters);
    return NextResponse.json(
      {
        success: true,
        requests: result.requests,
        total: result.total,
        limit: result.limit,
        offset: result.offset,
      },
      { status: 200 },
    );
  } catch (error) {
    const normalized = normalizeSignupGuardrailError(error, 'Unable to load signup requests.');
    return NextResponse.json(
      {
        success: false,
        error: normalized.message,
      },
      { status: normalized.status },
    );
  }
}

function parseStatus(value: string | null): SignupRequestStatusFilter | undefined {
  if (!value) {
    return undefined;
  }
  if (VALID_STATUSES.has(value as SignupRequestStatusFilter)) {
    return value as SignupRequestStatusFilter;
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

import { NextRequest, NextResponse } from 'next/server';

import { normalizeSignupGuardrailError } from '@/app/api/v1/auth/_utils/signupGuardrailResponses';
import { issueSignupInvite, listSignupInvites } from '@/lib/server/services/auth/signupGuardrails';
import type { IssueSignupInviteInput, SignupInviteStatusFilter } from '@/types/signup';

const VALID_STATUSES: ReadonlySet<SignupInviteStatusFilter> = new Set([
  'active',
  'revoked',
  'expired',
  'exhausted',
]);

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const filters = {
    status: parseStatus(url.searchParams.get('status')),
    email: normalizeString(url.searchParams.get('email')),
    requestId: normalizeString(url.searchParams.get('request_id')),
    limit: parseNumber(url.searchParams.get('limit')),
    offset: parseNumber(url.searchParams.get('offset')),
  };

  try {
    const result = await listSignupInvites(filters);
    return NextResponse.json(
      {
        success: true,
        invites: result.invites,
        total: result.total,
        limit: result.limit,
        offset: result.offset,
      },
      { status: 200 },
    );
  } catch (error) {
    const normalized = normalizeSignupGuardrailError(error, 'Unable to load signup invites.');
    return NextResponse.json(
      {
        success: false,
        error: normalized.message,
      },
      { status: normalized.status },
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const payload = (await request.json()) as IssueSignupInviteInput;
    const invite = await issueSignupInvite(payload);
    return NextResponse.json(
      {
        success: true,
        data: invite,
      },
      { status: 201 },
    );
  } catch (error) {
    const normalized = normalizeSignupGuardrailError(error, 'Unable to issue signup invite.');
    return NextResponse.json(
      {
        success: false,
        error: normalized.message,
      },
      { status: normalized.status },
    );
  }
}

function parseStatus(value: string | null): SignupInviteStatusFilter | undefined {
  if (!value) {
    return undefined;
  }
  if (VALID_STATUSES.has(value as SignupInviteStatusFilter)) {
    return value as SignupInviteStatusFilter;
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

function normalizeString(value: string | null): string | undefined {
  if (!value) {
    return undefined;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

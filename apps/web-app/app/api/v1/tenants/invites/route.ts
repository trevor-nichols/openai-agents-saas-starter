import { NextRequest, NextResponse } from 'next/server';

import {
  issueTeamInvite,
  listTeamInvites,
  TeamServiceError,
} from '@/lib/server/services/team';
import type { IssueTeamInviteInput, TeamInviteStatusFilter } from '@/types/team';

import { mapTeamErrorStatus } from '../_utils/errors';
import { parseLimitParam, parseOffsetParam } from '../_utils/pagination';

const VALID_STATUSES: ReadonlySet<TeamInviteStatusFilter> = new Set([
  'active',
  'accepted',
  'revoked',
  'expired',
]);

function parseStatus(value: string | null): TeamInviteStatusFilter | undefined {
  if (!value) return undefined;
  if (VALID_STATUSES.has(value as TeamInviteStatusFilter)) {
    return value as TeamInviteStatusFilter;
  }
  return undefined;
}

function normalizeEmail(value: string | null): string | undefined {
  if (!value) return undefined;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const limitResult = parseLimitParam(url.searchParams.get('limit'));
  const offsetResult = parseOffsetParam(url.searchParams.get('offset'));

  if (!limitResult.ok) {
    return NextResponse.json({ success: false, error: limitResult.error }, { status: 400 });
  }

  if (!offsetResult.ok) {
    return NextResponse.json({ success: false, error: offsetResult.error }, { status: 400 });
  }

  try {
    const payload = await listTeamInvites({
      status: parseStatus(url.searchParams.get('status')),
      email: normalizeEmail(url.searchParams.get('email')),
      limit: limitResult.value,
      offset: offsetResult.value,
    });

    return NextResponse.json(
      {
        success: true,
        invites: payload.invites,
        total: payload.total,
        limit: payload.limit,
        offset: payload.offset,
      },
      { status: 200 },
    );
  } catch (error) {
    if (error instanceof TeamServiceError) {
      return NextResponse.json({ success: false, error: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Unable to load team invites.';
    return NextResponse.json({ success: false, error: message }, { status: mapTeamErrorStatus(message) });
  }
}

export async function POST(request: NextRequest) {
  let payload: IssueTeamInviteInput | null = null;
  try {
    payload = (await request.json()) as IssueTeamInviteInput;
  } catch (_error) {
    payload = null;
  }

  if (!payload?.invitedEmail || !payload?.role) {
    return NextResponse.json(
      { success: false, error: 'Invited email and role are required.' },
      { status: 400 },
    );
  }

  try {
    const invite = await issueTeamInvite(payload);
    return NextResponse.json({ success: true, data: invite }, { status: 201 });
  } catch (error) {
    if (error instanceof TeamServiceError) {
      return NextResponse.json({ success: false, error: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Unable to issue team invite.';
    return NextResponse.json({ success: false, error: message }, { status: mapTeamErrorStatus(message) });
  }
}

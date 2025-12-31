import { NextRequest, NextResponse } from 'next/server';

import {
  addTeamMember,
  listTeamMembers,
  TeamServiceError,
} from '@/lib/server/services/team';
import type { AddTeamMemberInput } from '@/types/team';

import { mapTeamErrorStatus } from '../_utils/errors';
import { parseLimitParam, parseOffsetParam } from '../_utils/pagination';

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
    const payload = await listTeamMembers({ limit: limitResult.value, offset: offsetResult.value });
    return NextResponse.json(
      {
        success: true,
        members: payload.members,
        total: payload.total,
        ownerCount: payload.ownerCount,
        limit: payload.limit,
        offset: payload.offset,
      },
      { status: 200 },
    );
  } catch (error) {
    if (error instanceof TeamServiceError) {
      return NextResponse.json(
        { success: false, error: error.message },
        { status: error.status },
      );
    }
    const message = error instanceof Error ? error.message : 'Unable to load team members.';
    return NextResponse.json(
      { success: false, error: message },
      { status: mapTeamErrorStatus(message) },
    );
  }
}

export async function POST(request: NextRequest) {
  let payload: AddTeamMemberInput | null = null;
  try {
    payload = (await request.json()) as AddTeamMemberInput;
  } catch (_error) {
    payload = null;
  }

  if (!payload?.email || !payload?.role) {
    return NextResponse.json(
      { success: false, error: 'Email and role are required.' },
      { status: 400 },
    );
  }

  try {
    const member = await addTeamMember(payload);
    return NextResponse.json(
      { success: true, data: member },
      { status: 201 },
    );
  } catch (error) {
    if (error instanceof TeamServiceError) {
      return NextResponse.json(
        { success: false, error: error.message },
        { status: error.status },
      );
    }
    const message = error instanceof Error ? error.message : 'Unable to add team member.';
    return NextResponse.json(
      { success: false, error: message },
      { status: mapTeamErrorStatus(message) },
    );
  }
}

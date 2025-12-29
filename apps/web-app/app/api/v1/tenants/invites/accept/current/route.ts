import { NextRequest, NextResponse } from 'next/server';

import { acceptTeamInviteExisting, TeamServiceError } from '@/lib/server/services/team';

import { mapTeamErrorStatus } from '../../../_utils/errors';

export async function POST(request: NextRequest) {
  let token: string | null = null;
  try {
    const payload = (await request.json()) as { token?: string | null };
    token = typeof payload?.token === 'string' ? payload.token.trim() : null;
  } catch (_error) {
    token = null;
  }

  if (!token) {
    return NextResponse.json({ success: false, error: 'Invite token is required.' }, { status: 400 });
  }

  try {
    const invite = await acceptTeamInviteExisting({ token });
    return NextResponse.json({ success: true, data: invite }, { status: 200 });
  } catch (error) {
    if (error instanceof TeamServiceError) {
      return NextResponse.json({ success: false, error: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Unable to accept team invite.';
    return NextResponse.json({ success: false, error: message }, { status: mapTeamErrorStatus(message) });
  }
}

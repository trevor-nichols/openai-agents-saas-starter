import { NextRequest, NextResponse } from 'next/server';

import { revokeTeamInvite, TeamServiceError } from '@/lib/server/services/team';

import { mapTeamErrorStatus } from '../../../_utils/errors';

interface RouteContext {
  params: Promise<{ inviteId: string }>;
}

export async function POST(_request: NextRequest, context: RouteContext) {
  const { inviteId } = await context.params;
  if (!inviteId) {
    return NextResponse.json({ success: false, error: 'Invite id is required.' }, { status: 400 });
  }

  try {
    const invite = await revokeTeamInvite(inviteId);
    return NextResponse.json({ success: true, data: invite }, { status: 200 });
  } catch (error) {
    if (error instanceof TeamServiceError) {
      return NextResponse.json({ success: false, error: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Unable to revoke team invite.';
    return NextResponse.json({ success: false, error: message }, { status: mapTeamErrorStatus(message) });
  }
}

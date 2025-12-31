import { NextRequest, NextResponse } from 'next/server';

import { removeTeamMember, TeamServiceError } from '@/lib/server/services/team';

import { mapTeamErrorStatus } from '../../_utils/errors';

interface RouteContext {
  params: Promise<{ userId: string }>;
}

export async function DELETE(_request: NextRequest, context: RouteContext) {
  const { userId } = await context.params;
  if (!userId) {
    return NextResponse.json({ success: false, error: 'User id is required.' }, { status: 400 });
  }

  try {
    const payload = await removeTeamMember(userId);
    return NextResponse.json(
      { success: true, message: payload.message },
      { status: 200 },
    );
  } catch (error) {
    if (error instanceof TeamServiceError) {
      return NextResponse.json({ success: false, error: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Unable to remove team member.';
    return NextResponse.json({ success: false, error: message }, { status: mapTeamErrorStatus(message) });
  }
}

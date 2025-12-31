import { NextRequest, NextResponse } from 'next/server';

import { TeamServiceError, updateTeamMemberRole } from '@/lib/server/services/team';
import type { UpdateTeamMemberRoleInput } from '@/types/team';

import { mapTeamErrorStatus } from '../../../_utils/errors';

interface RouteContext {
  params: Promise<{ userId: string }>;
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  const { userId } = await context.params;
  if (!userId) {
    return NextResponse.json({ success: false, error: 'User id is required.' }, { status: 400 });
  }

  let payload: UpdateTeamMemberRoleInput | null = null;
  try {
    payload = (await request.json()) as UpdateTeamMemberRoleInput;
  } catch (_error) {
    payload = null;
  }

  if (!payload?.role) {
    return NextResponse.json({ success: false, error: 'Role is required.' }, { status: 400 });
  }

  try {
    const member = await updateTeamMemberRole(userId, payload);
    return NextResponse.json({ success: true, data: member }, { status: 200 });
  } catch (error) {
    if (error instanceof TeamServiceError) {
      return NextResponse.json({ success: false, error: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Unable to update member role.';
    return NextResponse.json({ success: false, error: message }, { status: mapTeamErrorStatus(message) });
  }
}

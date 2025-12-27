import { NextRequest, NextResponse } from 'next/server';

import type { UserEmailChangeRequest } from '@/lib/api/client/types.gen';
import { changeCurrentUserEmail, UserProfileApiError } from '@/lib/server/services/users';

export async function PATCH(request: NextRequest) {
  try {
    const payload = (await request.json()) as UserEmailChangeRequest;
    const result = await changeCurrentUserEmail(payload);
    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    if (error instanceof UserProfileApiError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to update email.';
    const normalized = message.toLowerCase();
    const status = normalized.includes('missing access token') || normalized.includes('missing credentials') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

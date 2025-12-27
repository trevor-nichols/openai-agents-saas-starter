import { NextRequest, NextResponse } from 'next/server';

import type { UserProfileUpdateRequest } from '@/lib/api/client/types.gen';
import { updateCurrentUserProfile } from '@/lib/server/services/users';
import { UserProfileApiError } from '@/lib/server/services/users.errors';

export async function PATCH(request: NextRequest) {
  try {
    const payload = (await request.json()) as UserProfileUpdateRequest;
    const profile = await updateCurrentUserProfile(payload);
    return NextResponse.json(profile, { status: 200 });
  } catch (error) {
    if (error instanceof UserProfileApiError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to update profile.';
    const normalized = message.toLowerCase();
    const status = normalized.includes('missing access token') || normalized.includes('missing credentials') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

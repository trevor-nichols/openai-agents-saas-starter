import { NextResponse } from 'next/server';

import { getCurrentUserProfile } from '@/lib/server/services/users';
import { UserProfileApiError } from '@/lib/server/services/users.errors';

export async function GET() {
  try {
    const profile = await getCurrentUserProfile();
    return NextResponse.json(profile);
  } catch (error) {
    if (error instanceof UserProfileApiError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to load user profile.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

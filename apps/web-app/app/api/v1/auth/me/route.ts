import { NextResponse } from 'next/server';

import { loadSessionSummary } from '@/lib/auth/session';
import { getCurrentUserProfile } from '@/lib/server/services/auth';

export async function GET() {
  const summary = await loadSessionSummary();
  if (!summary) {
    return NextResponse.json({ message: 'Not authenticated' }, { status: 401 });
  }

  try {
    return NextResponse.json({
      ...summary,
      profile: await getCurrentUserProfile(),
    });
  } catch (error) {
    return NextResponse.json(
      { message: error instanceof Error ? error.message : 'Failed to load profile.' },
      { status: 401 },
    );
  }
}

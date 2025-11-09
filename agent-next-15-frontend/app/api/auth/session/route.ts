import { NextResponse } from 'next/server';

import { authenticatedFetch } from '@/lib/auth/http';
import { loadSessionSummary } from '@/lib/auth/session';

export async function GET() {
  const summary = await loadSessionSummary();
  if (!summary) {
    return NextResponse.json({ message: 'Not authenticated' }, { status: 401 });
  }

  try {
    const response = await authenticatedFetch('/api/v1/auth/me', {
      method: 'GET',
    });
    const data = await response.json();
    return NextResponse.json({
      ...summary,
      profile: data?.data ?? data,
    });
  } catch (error) {
    return NextResponse.json(
      { message: error instanceof Error ? error.message : 'Failed to load profile.' },
      { status: 401 },
    );
  }
}

import { NextResponse } from 'next/server';

import { getBackendFeatureFlags } from '@/lib/server/features';

export async function GET() {
  try {
    const flags = await getBackendFeatureFlags();
    return NextResponse.json(flags);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load backend feature flags.';
    return NextResponse.json({ message }, { status: 502 });
  }
}

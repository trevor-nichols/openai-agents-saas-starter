import { NextResponse } from 'next/server';

import { getBackendFeatureFlags } from '@/lib/server/features';

export async function GET() {
  const flags = await getBackendFeatureFlags();
  return NextResponse.json(flags);
}

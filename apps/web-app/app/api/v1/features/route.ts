import { NextResponse } from 'next/server';

import { FeatureFlagsApiError, getBackendFeatureFlags } from '@/lib/server/features';

export async function GET() {
  try {
    const flags = await getBackendFeatureFlags();
    return NextResponse.json(flags);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load backend feature flags.';
    const status =
      error instanceof FeatureFlagsApiError
        ? error.status
        : typeof error === 'object' && error !== null && 'status' in error
          ? (error as { status?: number }).status ?? 502
          : 502;
    return NextResponse.json(
      {
        success: false,
        error: 'FeatureFlagsError',
        message,
      },
      { status },
    );
  }
}

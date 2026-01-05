import { NextResponse } from 'next/server';

import { FeatureFlagsApiError, requireBillingFeature } from '@/lib/server/features';
import { listBillingPlans } from '@/lib/server/services/billing';

export async function GET() {
  try {
    await requireBillingFeature();
    const plans = await listBillingPlans();
    return NextResponse.json({
      success: true,
      plans,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load billing plans.';
    const status =
      error instanceof FeatureFlagsApiError
        ? error.status
        : message.toLowerCase().includes('missing access token')
          ? 401
          : 500;
    return NextResponse.json(
      {
        success: false,
        error: message,
      },
      { status },
    );
  }
}

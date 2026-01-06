import { NextResponse } from 'next/server';

import { listBillingPlans } from '@/lib/server/services/billing';

export async function GET() {
  try {
    const plans = await listBillingPlans();
    return NextResponse.json({
      success: true,
      plans,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load billing plans.';
    const status =
      typeof error === 'object' && error !== null && 'status' in error
        ? (error as { status?: number }).status ?? 500
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

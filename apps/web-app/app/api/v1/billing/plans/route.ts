import { NextResponse } from 'next/server';

import { listBillingPlans } from '@/lib/server/services/billing';
import { billingEnabled } from '@/lib/config/features';

export async function GET() {
  if (!billingEnabled) {
    return NextResponse.json({ success: false, error: 'Billing is disabled.' }, { status: 404 });
  }
  try {
    const plans = await listBillingPlans();
    return NextResponse.json({
      success: true,
      plans,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load billing plans.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json(
      {
        success: false,
        error: message,
      },
      { status },
    );
  }
}

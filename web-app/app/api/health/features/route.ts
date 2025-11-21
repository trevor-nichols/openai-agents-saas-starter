import { NextResponse } from 'next/server';

import { billingEnabled } from '@/lib/config/features';

const TRUE_VALUES = new Set(['true', '1', 'yes']);

function parseBoolean(value?: string | null): boolean | null {
  if (value === undefined || value === null) return null;
  return TRUE_VALUES.has(value.toLowerCase()) ? true : false;
}

export async function GET() {
  const backendBilling = parseBoolean(process.env.ENABLE_BILLING);

  return NextResponse.json({
    success: true,
    billingEnabled,
    backendBillingEnabled: backendBilling,
    sources: {
      frontend: process.env.NEXT_PUBLIC_ENABLE_BILLING ?? null,
      backend: process.env.ENABLE_BILLING ?? null,
    },
  });
}

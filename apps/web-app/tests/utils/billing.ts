import { randomUUID } from 'node:crypto';

import type { Page } from '@playwright/test';

export interface UsageEventInput {
  tenantId: string;
  featureKey: string;
  quantity: number;
  unit?: string;
}

export async function recordUsageEvent(page: Page, input: UsageEventInput): Promise<void> {
  const now = new Date();
  const payload = {
    feature_key: input.featureKey,
    quantity: input.quantity,
    unit: input.unit ?? 'requests',
    period_start: now.toISOString(),
    period_end: new Date(now.getTime() + 60_000).toISOString(),
    idempotency_key: `pw-usage-${randomUUID()}`,
  };

  const response = await page.request.post(`/api/v1/billing/tenants/${input.tenantId}/usage`, {
    data: payload,
  });

  if (!response.ok()) {
    const text = await response.text();
    throw new Error(`Usage API ${response.status()}: ${text || 'Unknown error'}`);
  }
}

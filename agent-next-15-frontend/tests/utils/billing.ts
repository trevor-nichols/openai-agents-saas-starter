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

  const response = await page.evaluate(async ({ tenantId, body }) => {
    const endpoint = `/api/billing/tenants/${tenantId}/usage`;
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    const text = await res.text();
    return { ok: res.ok, status: res.status, text };
  }, { tenantId: input.tenantId, body: payload });

  if (!response.ok) {
    throw new Error(`Usage API ${response.status}: ${response.text || 'Unknown error'}`);
  }
}

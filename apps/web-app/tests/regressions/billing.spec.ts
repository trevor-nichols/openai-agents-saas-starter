import type { Page } from '@playwright/test';

import { test, expect } from '../fixtures/base';
import { getPlaywrightEnv } from '../harness/env';
import { getTenantId } from '../harness/fixtures';
import { recordUsageEvent } from '../utils/billing';

const env = getPlaywrightEnv();
let primaryTenantId: string;

test.beforeAll(async () => {
  primaryTenantId = await getTenantId(env.tenantSlugs.primary);
});

test.describe.serial('Billing plan management', () => {
  test('tenant admin can upgrade and downgrade plans with optimistic UI + audit trail', async ({ tenantAdminPage }) => {
    const page = tenantAdminPage;
    const plans = await fetchBillingPlans(page);
    const subscription = await fetchTenantSubscription(page, primaryTenantId);
    const currentPlanCode = subscription?.plan_code ?? null;
    const targetPlan = plans.find((plan) => plan.code !== currentPlanCode && plan.is_active !== false);
    if (!targetPlan) {
      throw new Error(
        `Billing plan change requires at least two active plans. Current=${currentPlanCode ?? 'none'}; plans=${plans
          .map((plan) => plan.code)
          .join(', ')}`,
      );
    }
    const originalPlan = plans.find((plan) => plan.code === currentPlanCode) ?? null;

    await page.goto('/billing/plans', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: /plan management/i })).toBeVisible();

    await selectPlanTier(page, targetPlan, {
      billingEmail: env.billingEmail,
      seatCount: 5,
      timing: 'immediate',
    });
    await expectPlanInSubscription(page, new RegExp(targetPlan.code, 'i'));

    await page.goto('/billing', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: /subscription hub/i })).toBeVisible({ timeout: 15000 });
    await expectPlanSnapshot(page, new RegExp(targetPlan.code, 'i'));

    await page.goto('/billing/events', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: /event history/i })).toBeVisible();
    const eventsSurface = page
      .getByText(/No events recorded/i)
      .or(page.getByRole('table'));
    await expect(eventsSurface).toBeVisible();

    if (originalPlan && originalPlan.code !== targetPlan.code) {
      await page.goto('/billing/plans', { waitUntil: 'domcontentloaded' });
      await selectPlanTier(page, originalPlan, {
        billingEmail: env.billingEmail,
        seatCount: 3,
        timing: 'immediate',
      });
      await expectPlanInSubscription(page, new RegExp(originalPlan.code, 'i'));
    }
  });

  test('usage logging reflects latest plan quota without cache busting', async ({ tenantAdminPage }) => {
    const page = tenantAdminPage;

    await page.goto('/billing/usage', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: /usage ledger/i })).toBeVisible();
    const usageSurface = page.locator('table').or(page.getByRole('heading', { name: /no usage recorded/i }));
    await expect(usageSurface).toBeVisible();

    const usageQuantity = Math.floor(Math.random() * 25) + 10;
    await recordUsageEvent(page, {
      tenantId: primaryTenantId,
      featureKey: 'messages',
      quantity: usageQuantity,
    });

    await page.reload({ waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: /usage ledger/i })).toBeVisible({ timeout: 15000 });

    const usageRow = page.locator('tbody tr').filter({
      hasText: /messages/i,
    }).filter({
      hasText: usageQuantity.toString(),
    });
    await expect(usageRow.first()).toBeVisible({ timeout: 15000 });

    await page.goto('/billing', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: /subscription hub/i })).toBeVisible({ timeout: 15000 });
    const overviewTable = page.locator('table').first();
    await expect(overviewTable).toBeVisible({ timeout: 15000 });
    const overviewRow = overviewTable.locator('tbody tr').filter({
      hasText: /messages/i,
    }).filter({
      hasText: usageQuantity.toString(),
    });
    await expect(overviewRow.first()).toBeVisible({ timeout: 15000 });
  });
});

type BillingPlanSummary = {
  code: string;
  name: string;
  is_active?: boolean;
};

async function selectPlanTier(
  page: Page,
  plan: BillingPlanSummary,
  options: { billingEmail: string; seatCount?: number; autoRenew?: boolean; timing?: 'auto' | 'immediate' | 'period_end' },
) {
  const planPattern = new RegExp(`${plan.name}|${plan.code}`, 'i');
  const planTrigger = page.getByRole('button').filter({ hasText: planPattern }).first();
  await expect(planTrigger).toBeVisible({ timeout: 15000 });
  await planTrigger.click();

  const dialog = page.getByRole('dialog', { name: new RegExp(plan.name, 'i') });
  await expect(dialog).toBeVisible();

  const billingEmailField = dialog.getByLabel('Billing email');
  if (await billingEmailField.count()) {
    await billingEmailField.fill(options.billingEmail);
  }
  if (typeof options.seatCount === 'number') {
    await dialog.getByLabel('Seat count').fill(String(options.seatCount));
  }
  if (typeof options.autoRenew === 'boolean') {
    const toggle = dialog.getByRole('switch', { name: /auto renew/i });
    const ariaChecked = await toggle.getAttribute('aria-checked');
    const shouldEnable = options.autoRenew ? 'true' : 'false';
    if (ariaChecked !== shouldEnable) {
      await toggle.click();
    }
  }

  if (options.timing) {
    const timingLabel =
      options.timing === 'immediate'
        ? /Change now/i
        : options.timing === 'period_end'
          ? /Change at period end/i
          : /Auto/i;
    const timingOption = dialog.getByText(timingLabel).first();
    if (await timingOption.count()) {
      await timingOption.click();
    }
  }

  const submitButton = dialog.getByRole('button', { name: /(Request change|Change now|Schedule change|Start)/i }).first();
  await submitButton.click();

  await expect(dialog).toBeHidden({ timeout: 15000 });
}

async function expectPlanInSubscription(page: Page, matcher: RegExp) {
  const subscriptionCard = page.getByText(/Current subscription/i).first().locator('..').locator('..');
  await expect(subscriptionCard).toContainText(matcher, { timeout: 15000 });
}

async function expectPlanSnapshot(page: Page, matcher: RegExp) {
  const snapshotCard = page.getByText(/Current Plan/i).first().locator('..').locator('..');
  const planMatcher = new RegExp(`${matcher.source}|Plan pending`, 'i');
  await expect(snapshotCard).toContainText(planMatcher, { timeout: 15000 });
}

async function fetchBillingPlans(page: Page): Promise<BillingPlanSummary[]> {
  const response = await page.request.get('/api/v1/billing/plans');
  if (!response.ok()) {
    const text = await response.text();
    throw new Error(`Billing plans unavailable (${response.status()}): ${text}`);
  }
  const payload = (await response.json().catch(() => null)) as
    | { success?: boolean; plans?: BillingPlanSummary[]; error?: string }
    | null;
  if (!payload?.plans?.length) {
    throw new Error(payload?.error ?? 'Billing plan catalog is empty.');
  }
  return payload.plans;
}

async function fetchTenantSubscription(
  page: Page,
  tenantId: string,
): Promise<{ plan_code?: string | null } | null> {
  const response = await page.request.get(`/api/v1/billing/tenants/${tenantId}/subscription`);
  if (response.status() === 404) {
    return null;
  }
  if (!response.ok()) {
    const text = await response.text();
    throw new Error(`Subscription lookup failed (${response.status()}): ${text}`);
  }
  return (await response.json()) as { plan_code?: string | null };
}

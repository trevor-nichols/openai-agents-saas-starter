import { test, expect } from '@playwright/test';

/**
 * These specs intentionally call test.skip() so CI stays green until the
 * supporting fixtures (tenants, plans, transcripts) are seeded. Each block
 * documents the workflow the team needs to automate once data is ready.
 */

test.describe('Billing plan management', () => {
  test('tenant admin can upgrade and downgrade plans with optimistic UI + audit trail', async ({ page }) => {
    test.skip('Waiting for seeded billing fixtures + automation account.');

    // TODO Platform Foundations
    // 1. Seed a tenant with Starter plan + valid billing metadata (Stripe stub ok).
    // 2. Log in as tenant admin and visit /billing.
    // 3. Use the plan card CTA or plan comparison table to upgrade to Scale.
    // 4. Assert toast + optimistic UI while mutation is pending.
    // 5. Verify billing events table receives SSE update, and plan summary reflects Scale.
    // 6. Downgrade back to Starter and ensure audit rows capture both transitions.
    await page.goto('/billing');
    await expect(page).toHaveTitle(/Billing/);
  });

  test('usage logging reflects latest plan quota without cache busting', async ({ page }) => {
    test.skip('Pending usage event fixtures + deterministic SSE stream.');

    // TODO steps: log usage, assert KPI/sse.
    await page.goto('/billing');
  });
});


test.describe('Service account lifecycle', () => {
  test('operator can issue and revoke Vault-signed service accounts', async ({ page }) => {
    test.skip('Needs Vault test signer + seeded automation tenant.');

    // Outline
    // 1. Login as platform operator (scope service_accounts:manage).
    // 2. Navigate to /account/service-accounts.
    // 3. Click "Issue token" (Vault option) and provide alias/ttl.
    // 4. Verify modal shows signed token + copy-to-clipboard.
    // 5. Revoke the freshly issued token and assert table updates + toast.
    await page.goto('/account/service-accounts');
  });

  test('tenant admin sees filtered list scoped to their tenant', async ({ page }) => {
    test.skip('Requires tenant-level fixtures for sessions + service accounts.');
    await page.goto('/account/service-accounts');
  });
});


test.describe('Chat transcript export', () => {
  test('user exports a conversation and download is available', async ({ page }) => {
    test.skip('Waiting for deterministic conversation fixture and storage bucket.');

    // Steps: login, open chat, select conversation, open drawer, click export, verify notification + file (maybe intercept).
    await page.goto('/chat');
  });
});

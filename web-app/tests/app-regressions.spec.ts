import fs from 'node:fs/promises';
import { randomUUID } from 'node:crypto';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import type { Download, Locator, Page } from '@playwright/test';

import { recordUsageEvent } from './utils/billing';
import { login } from './utils/auth';
import {
  getOperatorCredentials,
  getOperatorTenantSlug,
  getPrimaryTenantSlug,
  getTenantAdminCredentials,
} from './utils/credentials';
import { getConversationId, getTenantId } from './utils/fixtures';
import { getApiBaseUrl } from './utils/testEnv';

const adminCredentials = getTenantAdminCredentials();
const primaryTenantSlug = getPrimaryTenantSlug();
const operatorCredentials = getOperatorCredentials();
const operatorTenantSlug = getOperatorTenantSlug();
const billingContactEmail = process.env.PLAYWRIGHT_BILLING_EMAIL ?? 'billing+playwright@example.com';
const transcriptConversationKey = 'transcript-export-seed';
const archivedConversationKey = 'archived-conversation-seed';
const primaryTenantName = 'Playwright Starter Tenant';
const archivedConversationUserEmail = 'analyst@example.com';
const transcriptConversationSnippet = 'changelog emailed';
const archivedConversationSnippet = 'Restore anytime from the archive tab';

let primaryTenantId: string;
let operatorTenantId: string;
let transcriptConversationId: string;
let archivedConversationId: string;

test.beforeAll(async () => {
  primaryTenantId = await getTenantId(primaryTenantSlug);
  operatorTenantId = await getTenantId(operatorTenantSlug);
  transcriptConversationId = await getConversationId(primaryTenantSlug, transcriptConversationKey);
  archivedConversationId = await getConversationId(primaryTenantSlug, archivedConversationKey);
});

test.describe.serial('Billing plan management', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await login(page, adminCredentials);
  });

  test('tenant admin can upgrade and downgrade plans with optimistic UI + audit trail', async ({ page }) => {
    await page.goto('/billing/plans');
    await expect(page.getByRole('heading', { name: /plan management/i })).toBeVisible();

    await selectPlanTier(page, 'Scale', {
      billingEmail: billingContactEmail,
      seatCount: 5,
    });
    await expectCurrentPlan(page, /scale/i);

    await page.goto('/billing');
    await expectPlanSnapshot(page, /scale/i);
    await expect(page.getByText(/Subscription updated/i)).toBeVisible();

    await page.goto('/billing/events');
    await expect(page.getByRole('heading', { name: /event history/i })).toBeVisible();
    await expect(page.getByRole('table')).toContainText(/subscription/i);

    await page.goto('/billing/plans');
    await selectPlanTier(page, 'Starter', {
      billingEmail: billingContactEmail,
      seatCount: 3,
    });
    await expectCurrentPlan(page, /starter/i);
  });

  test('usage logging reflects latest plan quota without cache busting', async ({ page }) => {
    await page.goto('/billing/usage');
    await expect(page.getByRole('heading', { name: /usage ledger/i })).toBeVisible();
    await expect(page.locator('table')).toBeVisible();

    const usageQuantity = Math.floor(Math.random() * 25) + 10;
    await recordUsageEvent(page, {
      tenantId: primaryTenantId,
      featureKey: 'messages',
      quantity: usageQuantity,
    });

    const usageRow = page.locator('tbody tr').filter({
      hasText: /messages/i,
    }).filter({
      hasText: usageQuantity.toString(),
    });
    await expect(usageRow.first()).toBeVisible({ timeout: 15000 });

    await page.goto('/billing');
    await expect(page.getByText(/Live billing events/i)).toBeVisible();
    await expect(page.getByText(new RegExp(`${usageQuantity}\\s+units`))).toBeVisible({ timeout: 15000 });
  });
});


test.describe.serial('Service account lifecycle', () => {
  test('operator can issue and revoke Vault-signed service accounts', async ({ page }) => {
    await page.context().clearCookies();
    await login(page, operatorCredentials);
    await openServiceAccountsTab(page);

    const accountName = `ci-${randomUUID().slice(0, 8)}`;
    const reason = `Playwright coverage ${Date.now()}`;

    await page.getByRole('button', { name: /Issue token/i }).click();
    const issueDialog = page.getByRole('dialog', { name: /Issue a new service-account token/i });
    await expect(issueDialog).toBeVisible();
    await issueDialog.getByLabel('Account').fill(accountName);
    await issueDialog.getByLabel('Scopes').fill('chat:write,conversations:read');
    await issueDialog.getByLabel('Tenant ID').fill(primaryTenantId);
    await issueDialog.getByLabel('Lifetime (minutes)').fill('30');
    await issueDialog.getByLabel('Reason').fill(reason);
    await issueDialog.getByRole('button', { name: /Issue token/i }).click();

    const issuedDialog = page.getByRole('dialog', { name: /Copy your token now/i });
    await expect(issuedDialog).toBeVisible({ timeout: 10000 });
    await expect(issuedDialog.getByText(accountName)).toBeVisible();
    await issuedDialog.getByRole('button', { name: /Done/i }).click();

    const tokenRow = getServiceAccountRow(page, accountName);
    await expect(tokenRow).toBeVisible({ timeout: 15000 });

    await revokeServiceAccountToken(page, tokenRow, 'Playwright cleanup');
  });

  test('tenant admin sees filtered list scoped to their tenant', async ({ page }) => {
    await page.context().clearCookies();
    await login(page, adminCredentials);
    await openServiceAccountsTab(page);

    const accountName = `tenant-admin-${randomUUID().slice(0, 8)}`;
    await page.getByRole('button', { name: /Issue token/i }).click();
    const issueDialog = page.getByRole('dialog', { name: /Issue a new service-account token/i });
    await issueDialog.getByLabel('Account').fill(accountName);
    await issueDialog.getByLabel('Scopes').fill('chat:write');
    await issueDialog.getByLabel('Tenant ID').fill(operatorTenantId);
    await issueDialog.getByLabel('Reason').fill('Verifying tenant scoping for Playwright');
    await issueDialog.getByRole('button', { name: /Issue token/i }).click();
    await expect(issueDialog.getByText(/Tenant mismatch/i)).toBeVisible({ timeout: 10000 });

    await issueDialog.getByLabel('Tenant ID').fill(primaryTenantId);
    await issueDialog.getByRole('button', { name: /Issue token/i }).click();
    const issuedDialog = page.getByRole('dialog', { name: /Copy your token now/i });
    await issuedDialog.getByRole('button', { name: /Done/i }).click();

    const tokenRow = getServiceAccountRow(page, accountName);
    await expect(tokenRow).toBeVisible({ timeout: 15000 });

    const searchInput = page.getByPlaceholder('Search account');
    await searchInput.fill('no-matches-here');
    await expect(page.getByText(/No service-account tokens/i)).toBeVisible({ timeout: 10000 });
    await searchInput.fill(accountName);
    await expect(tokenRow).toBeVisible();
    await searchInput.fill('');

    await revokeServiceAccountToken(page, tokenRow, 'Tenant admin cleanup');
  });
});


test.describe.serial('Tenant settings management', () => {
  test('tenant admin updates billing contacts and webhook settings', async ({ page }) => {
    await page.context().clearCookies();
    await login(page, adminCredentials);
    await page.goto('/settings/tenant');
    await expect(page.getByRole('heading', { name: /Tenant controls/i })).toBeVisible({ timeout: 10000 });

    const contactName = `Playwright Contact ${randomUUID().slice(0, 6)}`;
    const contactEmail = `billing-${randomUUID().slice(0, 4)}@example.com`;

    await page.getByRole('button', { name: /Add contact/i }).first().click();
    await page.getByLabel('Name').last().fill(contactName);
    await page.getByLabel('Email').last().fill(contactEmail);
    await page.getByLabel('Role').last().fill('Finance lead');
    await page.getByLabel('Phone').last().fill('555-0100');
    const alertSwitch = page.getByRole('switch', { name: /Send billing alerts/i }).last();
    const alertChecked = await alertSwitch.getAttribute('aria-checked');
    if (alertChecked !== 'true') {
      await alertSwitch.click();
    }
    await page.getByRole('button', { name: /Save contacts/i }).click();
    await expect(page.getByText(/Billing contacts saved/i)).toBeVisible({ timeout: 10000 });

    await page.getByRole('button', { name: /Remove/i }).click();
    await page.getByRole('button', { name: /Save contacts/i }).click();
    await expect(page.getByText(/Billing contacts saved/i)).toBeVisible({ timeout: 10000 });

    const webhookUrl = `http://localhost:8787/webhook-echo?run=${Date.now()}`;
    await page.getByLabel('Webhook URL').fill(webhookUrl);
    await page.getByRole('button', { name: /Save webhook/i }).click();
    await expect(page.getByText(/Webhook updated/i)).toBeVisible({ timeout: 10000 });

    await page.getByRole('button', { name: /^Clear$/i }).click();
    await page.getByRole('button', { name: /Save webhook/i }).click();
    await expect(page.getByText(/Billing webhooks disabled/i)).toBeVisible({ timeout: 10000 });
  });
});


test.describe.serial('Chat transcript export', () => {
  test('user exports a conversation and download is available', async ({ page }) => {
    await page.context().clearCookies();
    await login(page, adminCredentials);
    await page.goto('/chat');

    const conversationButton = page.getByRole('button', { name: new RegExp(transcriptConversationSnippet, 'i') }).first();
    await expect(conversationButton).toBeVisible({ timeout: 10000 });
    await conversationButton.click();

    const detailButton = page.getByRole('button', { name: /Conversation details/i });
    await expect(detailButton).toBeEnabled({ timeout: 10000 });
    await detailButton.click();

    const drawer = page.getByRole('dialog', { name: /Conversation detail/i });
    await expect(drawer).toBeVisible({ timeout: 10000 });
    await expect(drawer.getByText(transcriptConversationId)).toBeVisible({ timeout: 10000 });

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      drawer.getByRole('button', { name: /Export JSON/i }).click(),
    ]);

    const payload = await readDownloadPayload(download);
    expect(payload.conversation_id).toBe(transcriptConversationId);
    await expect(page.getByText(/Export ready/i)).toBeVisible({ timeout: 10000 });
  });
});


test.describe.serial('Conversation archive management', () => {
  test('admin filters, deletes, and restores archived transcripts', async ({ page }) => {
    await page.context().clearCookies();
    await login(page, adminCredentials);
    await page.goto('/agents');
    await expect(page.getByRole('heading', { name: /Conversation archive/i })).toBeVisible({ timeout: 10000 });

    const archiveSearch = page.getByPlaceholder('Search by title, summary, or ID');
    await archiveSearch.fill('archived');
    const archiveRow = page.locator('table').locator('tr').filter({ hasText: archivedConversationSnippet }).first();
    await expect(archiveRow).toBeVisible({ timeout: 15000 });
    await archiveRow.click();

    const drawer = page.getByRole('dialog', { name: /Conversation detail/i });
    await expect(drawer.getByText(archivedConversationId)).toBeVisible({ timeout: 10000 });

    await drawer.getByRole('button', { name: /^Delete$/i }).click();
    const confirmDialog = page.getByRole('dialog', { name: /Delete this conversation/i });
    await expect(confirmDialog).toBeVisible({ timeout: 10000 });
    await confirmDialog.getByRole('button', { name: /Delete transcript/i }).click();

    await expect(page.getByText(/Conversation deleted/i)).toBeVisible({ timeout: 10000 });
    await expect(drawer).toBeHidden({ timeout: 10000 });

    await reseedArchivedConversation(page);
    await page.getByRole('button', { name: /^Refresh$/i }).first().click();
    await archiveSearch.fill('archived');
    await expect(
      page.locator('table').locator('tr').filter({ hasText: archivedConversationSnippet }).first(),
    ).toBeVisible({ timeout: 20000 });
  });
});

async function selectPlanTier(
  page: Page,
  planName: string,
  options: { billingEmail: string; seatCount?: number; autoRenew?: boolean },
) {
  const planTrigger = page.getByRole('button', { name: new RegExp(planName, 'i') }).first();
  await expect(planTrigger).toBeVisible();
  await planTrigger.click();

  const dialog = page.getByRole('dialog', { name: new RegExp(planName, 'i') });
  await expect(dialog).toBeVisible();

  await dialog.getByLabel('Billing email').fill(options.billingEmail);
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

  const submitButton = dialog.getByRole('button', { name: /(Move to|Update plan)/i }).first();
  await Promise.all([
    dialog.waitFor({ state: 'detached' }),
    submitButton.click(),
  ]);

  await expect(page.getByText(/Subscription updated/i)).toBeVisible({ timeout: 10000 });
}

async function expectCurrentPlan(page: Page, matcher: RegExp) {
  const cardTitle = page.getByText(/Current subscription/i).first();
  const planHeading = cardTitle.locator('xpath=../../..//h2').first();
  await expect(planHeading).toHaveText(matcher);
}

async function expectPlanSnapshot(page: Page, matcher: RegExp) {
  const snapshotLabel = page.getByText(/Current plan/i).first();
  const planValue = snapshotLabel.locator('xpath=../..//p[contains(@class,"text-2xl")]').first();
  await expect(planValue).toHaveText(matcher);
}

async function openServiceAccountsTab(page: Page) {
  await page.goto('/account?tab=automation');
  await expect(page.getByRole('heading', { name: /Service-account tokens/i })).toBeVisible({ timeout: 10000 });
}

function getServiceAccountRow(page: Page, accountName: string): Locator {
  return page.locator('table').locator('tr').filter({ hasText: accountName });
}

async function revokeServiceAccountToken(page: Page, row: Locator, reason: string) {
  await row.getByRole('button', { name: /Revoke/i }).click();
  const revokeDialog = page.getByRole('dialog', { name: /Revoke/i });
  await expect(revokeDialog).toBeVisible();
  const reasonField = revokeDialog.getByPlaceholder(/Optional reason/i);
  await reasonField.fill(reason);
  await revokeDialog.getByRole('button', { name: /Revoke token/i }).click();
  await expect(page.getByText(/Token revoked/i)).toBeVisible({ timeout: 10000 });
  await expect(row.getByText(/Revoked/i)).toBeVisible({ timeout: 10000 });
}

async function readDownloadPayload(download: Download) {
  let filePath = await download.path();
  if (!filePath) {
    const tempDir = path.join(process.cwd(), '.playwright-downloads');
    await fs.mkdir(tempDir, { recursive: true });
    filePath = path.join(tempDir, `${Date.now()}-${download.suggestedFilename()}`);
    await download.saveAs(filePath);
  }
  const fileContents = await fs.readFile(filePath, 'utf8');
  return JSON.parse(fileContents) as { conversation_id: string };
}

async function reseedArchivedConversation(page: Page) {
  const payload = {
    tenants: [
      {
        slug: primaryTenantSlug,
        name: primaryTenantName,
        conversations: [
          {
            key: archivedConversationKey,
            status: 'archived',
            user_email: archivedConversationUserEmail,
            messages: [
              { role: 'user', text: 'Archive this conversation for retention policy validation.' },
              { role: 'assistant', text: 'Conversation archived. Restore anytime from the archive tab.' },
            ],
          },
        ],
      },
    ],
  };

  const apiBase = getApiBaseUrl();
  const response = await page.request.post(`${apiBase}/api/v1/test-fixtures/apply`, {
    data: payload,
  });

  if (!response.ok()) {
    const body = await response.text();
    throw new Error(`Failed to reseed archived conversation (${response.status()}): ${body}`);
  }
}

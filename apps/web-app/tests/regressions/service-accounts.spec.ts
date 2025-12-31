import { randomUUID } from 'node:crypto';

import type { Locator, Page } from '@playwright/test';

import { test, expect } from '../fixtures/base';
import { getPlaywrightEnv } from '../harness/env';
import { getTenantId } from '../harness/fixtures';

const env = getPlaywrightEnv();
const operatorAccount = 'synthetic-monitor';
const operatorScopes = 'conversations:write,tools:read';
const adminAccount = 'analytics-batch';
const adminScopes = 'conversations:read';

let primaryTenantId: string;
let operatorTenantId: string;

test.beforeAll(async () => {
  primaryTenantId = await getTenantId(env.tenantSlugs.primary);
  operatorTenantId = await getTenantId(env.tenantSlugs.operator);
});

test.describe.serial('Service account lifecycle (operator)', () => {
  test('operator can issue and revoke Vault-signed service accounts', async ({ operatorPage }) => {
    const page = operatorPage;
    await openServiceAccountsTab(page);

    const accountName = operatorAccount;
    const reason = `Playwright coverage ${Date.now()}`;
    const fingerprint = `pw-${randomUUID().slice(0, 8)}`;

    await page.getByRole('button', { name: /Issue token/i }).click();
    const issueDialog = page.getByRole('dialog', { name: /Issue a new service-account token/i });
    await expect(issueDialog).toBeVisible();
    await issueDialog.getByLabel('Account').fill(accountName);
    await issueDialog.getByLabel('Scopes').fill(operatorScopes);
    await issueDialog.getByLabel('Tenant ID').fill(operatorTenantId);
    await issueDialog.getByLabel('Lifetime (minutes)').fill('30');
    await issueDialog.getByLabel('Fingerprint (optional)').fill(fingerprint);
    await ensureForceIssuance(issueDialog);
    await issueDialog.getByLabel('Reason').fill(reason);
    await submitIssueDialog(issueDialog);

    const issuedDialog = page.getByRole('dialog', { name: /Copy your token now/i });
    await expect(issuedDialog).toBeVisible({ timeout: 10000 });
    await expect(issuedDialog.getByText(accountName)).toBeVisible();
    await issuedDialog.getByRole('button', { name: /Done/i }).click();

    await refreshServiceAccountTokens(page);
    await filterServiceAccountTokens(page, accountName);
    const tokenRow = getServiceAccountRow(page, accountName, fingerprint);
    await expect(tokenRow).toBeVisible({ timeout: 15000 });

    await revokeServiceAccountToken(page, tokenRow, 'Playwright cleanup');
  });
});

test.describe.serial('Service account lifecycle (tenant admin)', () => {
  test('tenant admin sees filtered list scoped to their tenant', async ({ tenantAdminPage }) => {
    const page = tenantAdminPage;
    await openServiceAccountsTab(page);

    const accountName = adminAccount;
    const fingerprint = `pw-admin-${randomUUID().slice(0, 8)}`;
    await page.getByRole('button', { name: /Issue token/i }).click();
    const issueDialog = page.getByRole('dialog', { name: /Issue a new service-account token/i });
    await issueDialog.getByLabel('Account').fill(accountName);
    await issueDialog.getByLabel('Scopes').fill(adminScopes);
    await issueDialog.getByLabel('Tenant ID').fill(operatorTenantId);
    await issueDialog.getByLabel('Fingerprint (optional)').fill(fingerprint);
    await ensureForceIssuance(issueDialog);
    await issueDialog.getByLabel('Reason').fill('Verifying tenant scoping for Playwright');
    await submitIssueDialog(issueDialog);
    await expect(page.getByText(/Tenant mismatch/i)).toBeVisible({ timeout: 10000 });

    await issueDialog.getByLabel('Tenant ID').fill(primaryTenantId);
    await ensureForceIssuance(issueDialog);
    await submitIssueDialog(issueDialog);
    const issuedDialog = page.getByRole('dialog', { name: /Copy your token now/i });
    await issuedDialog.getByRole('button', { name: /Done/i }).click();

    await refreshServiceAccountTokens(page);
    await filterServiceAccountTokens(page, accountName);
    const tokenRow = getServiceAccountRow(page, accountName, fingerprint);
    await expect(tokenRow).toBeVisible({ timeout: 15000 });

    const searchInput = page.getByPlaceholder('Search account');
    const noMatchResponse = waitForTokenListResponse(page);
    await searchInput.fill('no-matches-here');
    await expect(searchInput).toHaveValue('no-matches-here');
    await noMatchResponse;
    await expect(page.getByText(/No service-account tokens/i)).toBeVisible({ timeout: 10000 });
    await filterServiceAccountTokens(page, accountName);
    await expect(tokenRow).toBeVisible();
    await searchInput.fill('');
    await expect(searchInput).toHaveValue('');

    await revokeServiceAccountToken(page, tokenRow, 'Tenant admin cleanup');
  });
});

async function openServiceAccountsTab(page: Page) {
  await page.goto('/account?tab=automation');
  await expect(page.getByRole('heading', { name: /Service-account tokens/i })).toBeVisible({ timeout: 10000 });
  await setStatusFilter(page, 'All');
}

function getServiceAccountRow(page: Page, accountName: string, fingerprint?: string): Locator {
  let row = page.locator('table').locator('tr').filter({ hasText: accountName });
  if (fingerprint) {
    row = row.filter({ hasText: fingerprint });
  }
  return row.first();
}

async function revokeServiceAccountToken(page: Page, row: Locator, reason: string) {
  await row.getByRole('button', { name: /Revoke/i }).click();
  const revokeDialog = page.getByRole('alertdialog', { name: /Revoke/i });
  await expect(revokeDialog).toBeVisible();
  const reasonField = revokeDialog.getByPlaceholder(/Optional reason/i);
  await reasonField.fill(reason);
  const revokeResponse = page.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/auth/service-accounts/tokens/') &&
      response.url().includes('/revoke') &&
      response.request().method() === 'POST' &&
      response.status() === 200,
  );
  await revokeDialog.getByRole('button', { name: /Revoke token/i }).click();
  await revokeResponse;
  await refreshServiceAccountTokens(page);
  await expect(row.getByText(/Revoked/i)).toBeVisible({ timeout: 10000 });
}

async function submitIssueDialog(issueDialog: Locator) {
  const submitButton = issueDialog.getByRole('button', { name: /Issue token/i });
  await submitButton.scrollIntoViewIfNeeded();
  await submitButton.click();
}

async function ensureForceIssuance(issueDialog: Locator) {
  const toggle = issueDialog.getByRole('switch', { name: /Force issuance/i });
  const checked = await toggle.getAttribute('aria-checked');
  if (checked !== 'true') {
    await toggle.click();
  }
}

async function refreshServiceAccountTokens(page: Page) {
  const refreshResponse = waitForTokenListResponse(page);
  await page.getByRole('button', { name: /^Refresh$/i }).click();
  await refreshResponse;
}

async function filterServiceAccountTokens(page: Page, accountName: string) {
  const searchInput = page.getByPlaceholder('Search account');
  const currentValue = await searchInput.inputValue();
  if (currentValue === accountName) {
    return;
  }
  const response = waitForTokenListResponse(page, 10_000).catch(() => null);
  await searchInput.fill(accountName);
  await expect(searchInput).toHaveValue(accountName);
  await response;
}

async function setStatusFilter(page: Page, label: string) {
  const trigger = page.getByRole('combobox').first();
  await trigger.click();
  const response = waitForTokenListResponse(page);
  await page.getByRole('option', { name: new RegExp(label, 'i') }).click();
  await response;
}

function waitForTokenListResponse(page: Page, timeout = 15_000) {
  return page.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/auth/service-accounts/tokens') &&
      response.request().method() === 'GET' &&
      response.status() === 200,
    { timeout },
  );
}

import { randomUUID } from 'node:crypto';

import type { Page } from '@playwright/test';

import { test, expect } from '../fixtures/base';

test('tenant admin can open team settings', async ({ tenantAdminPage }) => {
  const page = tenantAdminPage;
  await page.goto('/settings/team');
  await expect(page.getByRole('heading', { name: /team management/i })).toBeVisible();
  await expect(page.getByRole('tab', { name: /members/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /add member/i })).toBeVisible();

  await page.getByRole('tab', { name: /invites/i }).click();
  await expect(page.getByRole('button', { name: /issue invite/i })).toBeVisible();
});

test('invited user can accept invite and set password', async ({ tenantAdminPage, browser, env }) => {
  const page = tenantAdminPage;
  const inviteEmail = `invite+${randomUUID()}@example.com`;
  const inviteToken = await issueInviteToken(page, inviteEmail);

  const anonContext = await browser.newContext({
    baseURL: env.baseUrl,
    storageState: { cookies: [], origins: [] },
  });
  const anonPage = await anonContext.newPage();

  await anonPage.goto(`${env.baseUrl}/accept-invite?token=${encodeURIComponent(inviteToken)}`);

  await expect(anonPage.getByRole('heading', { name: /accept your invite/i })).toBeVisible();
  await expect(anonPage.getByLabel(/invite token/i)).toHaveValue(inviteToken);

  const password = `Playwright!${randomUUID().slice(0, 8)}1`;
  const passwordField = await fillInputValue(anonPage, 'input[name="password"]', password);
  const confirmField = await fillInputValue(anonPage, 'input[name="confirmPassword"]', password);
  await expect(passwordField).toHaveValue(password);
  await expect(confirmField).toHaveValue(password);

  await Promise.all([
    anonPage.waitForURL(/\/dashboard$/),
    anonPage.getByRole('button', { name: /accept invite/i }).click(),
  ]);

  await expect(anonPage.getByRole('heading', { name: /command center/i })).toBeVisible();
  await anonContext.close();
});

async function fillInputValue(page: Page, selector: string, value: string) {
  const locator = page.locator(selector);
  await expect(locator).toBeVisible();
  const deadline = Date.now() + 5000;
  while (Date.now() < deadline) {
    await locator.fill(value);
    if ((await locator.inputValue()) === value) {
      return locator;
    }
    await page.waitForTimeout(100);
  }
  return locator;
}

async function issueInviteToken(page: Page, invitedEmail: string): Promise<string> {
  const response = await page.request.post('/api/v1/tenants/invites', {
    data: { invitedEmail, role: 'member' },
  });

  const payload = (await response.json().catch(() => null)) as
    | { success?: boolean; data?: { inviteToken?: string } }
    | null;

  if (!response.ok() || payload?.success === false) {
    const text = payload ? JSON.stringify(payload) : await response.text();
    throw new Error(`Invite issue failed (${response.status()}): ${text || 'No response body'}`);
  }

  const token = payload?.data?.inviteToken as string | undefined;
  if (!token) {
    throw new Error('Invite issue response missing inviteToken.');
  }
  return token;
}

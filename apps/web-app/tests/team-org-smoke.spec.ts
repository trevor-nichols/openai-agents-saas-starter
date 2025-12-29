import { randomUUID } from 'node:crypto';

import { expect, test, type Page } from '@playwright/test';

import { login } from './utils/auth';
import { getTenantAdminCredentials } from './utils/credentials';

const adminCredentials = getTenantAdminCredentials();

async function issueInviteToken(page: Page, invitedEmail: string): Promise<string> {
  const response = await page.evaluate(async ({ email }) => {
    const res = await fetch('/api/v1/tenants/invites', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ invitedEmail: email, role: 'member' }),
    });
    const text = await res.text();
    return { ok: res.ok, status: res.status, text };
  }, { email: invitedEmail });

  if (!response.ok) {
    throw new Error(`Invite issue failed (${response.status}): ${response.text || 'No response body'}`);
  }

  let payload: any = null;
  try {
    payload = JSON.parse(response.text);
  } catch (_error) {
    throw new Error(`Invite issue returned non-JSON payload: ${response.text}`);
  }

  const token = payload?.data?.inviteToken as string | undefined;
  if (!token) {
    throw new Error('Invite issue response missing inviteToken.');
  }
  return token;
}

test('tenant admin can open team settings', async ({ page }) => {
  await page.context().clearCookies();
  await login(page, adminCredentials);

  await page.goto('/settings/team');
  await expect(page.getByRole('heading', { name: /team management/i })).toBeVisible();
  await expect(page.getByRole('tab', { name: /members/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /add member/i })).toBeVisible();

  await page.getByRole('tab', { name: /invites/i }).click();
  await expect(page.getByRole('button', { name: /issue invite/i })).toBeVisible();
});

test('invited user can accept invite and set password', async ({ page }) => {
  await page.context().clearCookies();
  await login(page, adminCredentials);

  const inviteEmail = `invite+${randomUUID().slice(0, 8)}@example.com`;
  const inviteToken = await issueInviteToken(page, inviteEmail);

  await page.context().clearCookies();
  await page.goto(`/accept-invite?token=${encodeURIComponent(inviteToken)}`);

  await expect(page.getByRole('heading', { name: /accept your invite/i })).toBeVisible();
  await expect(page.getByLabel(/invite token/i)).toHaveValue(inviteToken);

  const password = `Playwright!${randomUUID().slice(0, 8)}1`;
  await page.getByLabel('Create password').fill(password);
  await page.getByLabel('Confirm password').fill(password);

  await Promise.all([
    page.waitForURL(/\/dashboard$/),
    page.getByRole('button', { name: /accept invite/i }).click(),
  ]);

  await expect(page.getByRole('heading', { name: /tenant overview/i })).toBeVisible();
});

import { test, expect } from '@playwright/test';

import { buildSignupAccount, issueEmailVerificationToken } from './utils/signup';
import { isPublicSignupEnabled } from './utils/testEnv';

const PUBLIC_SIGNUP_ENABLED = isPublicSignupEnabled();

test.skip(!PUBLIC_SIGNUP_ENABLED, 'Public signup disabled. Set ALLOW_PUBLIC_SIGNUP=true to run this spec.');

test.describe('Self-serve signup + email verification', () => {
  test('new tenant registers, verifies email, and re-authenticates', async ({ page }) => {
    const account = buildSignupAccount();

    await test.step('complete the registration form', async () => {
      await page.goto('/register');
      await expect(page).toHaveTitle(/Create account/i);

      await page.getByLabel('Full name').fill(account.fullName);
      await page.getByLabel('Organization').fill(account.organization);
      await page.getByLabel('Email').fill(account.email);
      await page.getByLabel('Password').fill(account.password);
      await page.getByRole('checkbox', { name: /I agree to the/i }).check({ force: true });

      const submit = page.getByRole('button', { name: 'Create account' });
      await Promise.all([
        page.waitForURL(/\/dashboard$/),
        submit.click(),
      ]);
    });

    await test.step('verify dashboard loads for the newly created tenant', async () => {
      await expect(page).toHaveURL(/\/dashboard$/);
      await expect(page.getByRole('heading', { name: /Tenant overview/i })).toBeVisible();
    });

    await test.step('issue and redeem email verification token', async () => {
      const tokenPayload = await issueEmailVerificationToken(account.email);
      await page.goto(`/email/verify?token=${encodeURIComponent(tokenPayload.token)}`);
      await expect(page.getByText('Verified', { exact: true })).toBeVisible();
    });

    await test.step('logout from the onboarding session', async () => {
      await page.goto('/dashboard');
      await page.getByRole('button', { name: /Logout/i }).click();
      await expect(page).toHaveURL(/\/login$/);
    });

    await test.step('sign back in with the verified account', async () => {
      await page.getByLabel('Email').fill(account.email);
      await page.getByLabel('Password').fill(account.password);
      await page.getByRole('button', { name: 'Sign In' }).click();
      await expect(page).toHaveURL(/\/dashboard$/);
      await expect(page.getByRole('heading', { name: /Tenant overview/i })).toBeVisible();
    });
  });
});

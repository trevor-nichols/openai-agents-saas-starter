import { expect, type Page } from '@playwright/test';

import type { LoginCredentials } from './credentials';

export async function login(page: Page, creds: LoginCredentials): Promise<void> {
  await page.goto('/login');
  await page.getByLabel('Email').fill(creds.email);
  await page.getByLabel('Password').fill(creds.password);
  await Promise.all([
    page.waitForURL(/\/dashboard$/),
    page.getByRole('button', { name: /sign in/i }).click(),
  ]);
  await expect(page.getByRole('heading', { name: /tenant overview/i })).toBeVisible();
}

export async function logout(page: Page): Promise<void> {
  await page.goto('/chat');
  const logoutButton = page.getByRole('button', { name: /logout/i });
  if (await logoutButton.isVisible()) {
    await logoutButton.click();
    await page.waitForURL(/\/login$/);
  } else {
    await page.context().clearCookies();
  }
}

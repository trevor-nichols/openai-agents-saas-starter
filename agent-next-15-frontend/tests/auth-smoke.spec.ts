import { test, expect } from '@playwright/test';

const email = 'user@example.com';
const password = 'SuperSecret123!';

test('login, open chat, logout flow', async ({ page }) => {
  await page.goto('/login');

  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign In' }).click();

  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByText('Anything Agent Chat')).toBeVisible();

  await page.getByRole('button', { name: 'New' }).click();
  await page.getByRole('textbox').fill('Hello, agent!');
  await page.getByRole('button', { name: 'Send' }).click();

  await page.getByRole('button', { name: 'Logout' }).click();
  await expect(page).toHaveURL(/\/login$/);
});

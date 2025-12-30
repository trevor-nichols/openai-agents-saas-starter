import { test, expect } from '../fixtures/base';
import { waitForAppReady } from '../utils/appReady';

test('login, open chat, logout flow', async ({ page, env }) => {
  const { email, password } = env.tenantAdmin;

  await page.goto('/login');

  await expect(page.getByRole('heading', { name: /sign in to acme/i })).toBeVisible({ timeout: 15000 });

  const emailField = page.getByPlaceholder('you@example.com');
  await expect(emailField).toBeVisible({ timeout: 10000 });
  await emailField.fill(email);
  await expect(emailField).toHaveValue(email);

  const passwordField = page.getByPlaceholder('••••••••');
  await expect(passwordField).toBeVisible({ timeout: 10000 });
  await passwordField.fill(password);
  await expect(passwordField).toHaveValue(password);

  await Promise.all([
    page.waitForURL(/\/dashboard$/, { timeout: 20000 }),
    page.getByRole('button', { name: /sign in/i }).click(),
  ]);

  await expect(page.getByRole('heading', { name: /command center/i })).toBeVisible({ timeout: 15000 });

  await page.goto('/chat', { waitUntil: 'domcontentloaded' });
  await waitForAppReady(page);
  await expect(page.getByRole('heading', { name: /agent chat/i })).toBeVisible({ timeout: 15000 });

  await page.getByRole('button', { name: /new chat/i }).click();
  const composer = page.locator('textarea[name="message"]');
  await composer.fill('Hello, agent!');
  await composer.press('Enter');
  await expect(page.getByText('Hello, agent!')).toBeVisible({ timeout: 10000 });

  await page
    .getByRole('button', { name: /playwright admin|user@example\.com|signed in user/i })
    .click();
  await page.getByRole('menuitem', { name: /log out/i }).click();
  await expect(page).toHaveURL(/\/login$/, { timeout: 15000 });
});

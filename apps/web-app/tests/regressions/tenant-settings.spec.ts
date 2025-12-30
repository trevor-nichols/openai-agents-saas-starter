import { randomUUID } from 'node:crypto';

import { test, expect } from '../fixtures/base';

test.describe.serial('Tenant settings management', () => {
  test('tenant admin updates billing contacts and webhook settings', async ({ tenantAdminPage }) => {
    const page = tenantAdminPage;
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

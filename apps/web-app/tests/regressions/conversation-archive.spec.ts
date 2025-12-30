import type { Page } from '@playwright/test';

import { test, expect } from '../fixtures/base';
import { waitForAppReady } from '../utils/appReady';

const archivedConversationKey = 'archived-conversation-seed';
const primaryTenantName = 'Playwright Starter Tenant';
const archivedConversationUserEmail = 'analyst@example.com';
const archivedConversationSnippet = 'Restore anytime from the archive tab';

test.describe.serial('Conversation archive management', () => {
  test('admin filters, deletes, and restores archived transcripts', async ({ tenantAdminPage, apiBaseUrl, env }) => {
    const page = tenantAdminPage;
    await reseedArchivedConversation(page, apiBaseUrl, env.tenantSlugs.primary);
    await page.goto('/agents', { waitUntil: 'domcontentloaded' });
    await waitForAppReady(page, 30_000);
    await openArchivePanel(page);
    await expect(page.getByRole('heading', { name: /Conversation archive/i })).toBeVisible({ timeout: 20000 });

    let searchInput = page.getByPlaceholder('Search by title, summary, or ID');
    await expect(searchInput).toBeVisible();
    await expect(searchInput).toBeEditable();
    await searchInput.fill(archivedConversationSnippet);
    await expect(searchInput).toHaveValue(archivedConversationSnippet);

    const archiveRow = page.locator('table').locator('tbody tr').filter({ hasText: archivedConversationSnippet }).first();
    await expect(archiveRow).toBeVisible({ timeout: 15000 });
    await archiveRow.click();

    const drawer = page.getByRole('dialog', { name: /Conversation detail/i });
    await expect(drawer).toBeVisible({ timeout: 10000 });
    await expect(drawer.getByRole('button', { name: /Export JSON/i })).toBeEnabled({ timeout: 20000 });

    await drawer.getByRole('button', { name: /^Delete$/i }).click();
    const confirmDialog = page.getByRole('alertdialog', { name: /Delete this conversation/i });
    await expect(confirmDialog).toBeVisible({ timeout: 10000 });
    await confirmDialog.getByRole('button', { name: /Delete transcript/i }).click();

    await expect(page.getByText(/Conversation deleted/i)).toBeVisible({ timeout: 10000 });
    await expect(drawer).toBeHidden({ timeout: 10000 });

    await reseedArchivedConversation(page, apiBaseUrl, env.tenantSlugs.primary);
    await page.reload({ waitUntil: 'domcontentloaded' });
    await waitForAppReady(page, 30_000);
    await openArchivePanel(page);
    await expect(page.getByRole('heading', { name: /Conversation archive/i })).toBeVisible({ timeout: 20000 });
    searchInput = page.getByPlaceholder('Search by title, summary, or ID');
    await expect(searchInput).toBeVisible();
    await searchInput.fill(archivedConversationSnippet);
    await expect(searchInput).toHaveValue(archivedConversationSnippet);
    await expect(
      page.locator('table').locator('tbody tr').filter({ hasText: archivedConversationSnippet }).first(),
    ).toBeVisible({ timeout: 20000 });
  });
});

async function openArchivePanel(page: Page) {
  const insightsCard = page.getByRole('heading', { name: /Workspace Insights/i }).locator('..').locator('..');
  const archiveTrigger = insightsCard.getByRole('button', { name: /^Archive$/i });
  await expect(archiveTrigger).toBeVisible({ timeout: 15000 });

  const archiveTab = page.getByRole('tab', { name: /^Archive$/i });
  for (let attempt = 0; attempt < 3; attempt += 1) {
    await archiveTrigger.click();
    if (await archiveTab.isVisible()) {
      return archiveTab;
    }
    await page.waitForTimeout(500);
  }

  await expect(archiveTab).toBeVisible({ timeout: 20000 });
  return archiveTab;
}

async function reseedArchivedConversation(page: Page, apiBaseUrl: string, tenantSlug: string) {
  const payload = {
    tenants: [
      {
        slug: tenantSlug,
        name: primaryTenantName,
        users: [
          {
            email: archivedConversationUserEmail,
            password: 'Playwright-Archive-Seed-1!',
            display_name: 'Archive Analyst',
            role: 'member',
          },
        ],
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

  const response = await page.request.post(`${apiBaseUrl}/api/v1/test-fixtures/apply`, {
    data: payload,
  });

  if (!response.ok()) {
    const body = await response.text();
    throw new Error(`Failed to reseed archived conversation (${response.status()}): ${body}`);
  }
}

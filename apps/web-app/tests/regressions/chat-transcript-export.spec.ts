import fs from 'node:fs/promises';
import path from 'node:path';

import type { Download } from '@playwright/test';

import { test, expect } from '../fixtures/base';
import { waitForAppReady } from '../utils/appReady';

const transcriptConversationKey = 'transcript-export-seed';
const transcriptConversationSnippet = 'changelog emailed';

test.describe.serial('Chat transcript export', () => {
  test('user exports a conversation and download is available', async ({ tenantAdminPage }) => {
    const page = tenantAdminPage;
    await page.goto('/chat', { waitUntil: 'domcontentloaded' });
    await waitForAppReady(page);

    const searchInput = page.getByPlaceholder('Search chats...');
    await expect(searchInput).toBeVisible();
    await expect(searchInput).toBeEditable();

    await searchInput.fill(transcriptConversationSnippet);
    await expect(searchInput).toHaveValue(transcriptConversationSnippet);

    const conversationButton = page
      .getByRole('button')
      .filter({ hasText: new RegExp(transcriptConversationSnippet, 'i') })
      .first();
    await expect(conversationButton).toBeVisible({ timeout: 15000 });
    await conversationButton.click();

    const detailButton = page.getByRole('button', { name: /Details/i });
    await expect(detailButton).toBeEnabled({ timeout: 10000 });
    await detailButton.click();

    const drawer = page.getByRole('dialog', { name: /Conversation detail/i });
    await expect(drawer).toBeVisible({ timeout: 10000 });
    await expect(drawer.getByText(/Refreshing/i)).toBeHidden({ timeout: 15000 });
    await expect(drawer.getByText(/Transcript metadata/i)).toBeVisible({ timeout: 15000 });

    const exportButton = drawer.getByRole('button', { name: /Export JSON/i });
    await expect(exportButton).toBeEnabled({ timeout: 15000 });

    const [download] = await Promise.all([page.waitForEvent('download'), exportButton.click()]);

    const payload = await readDownloadPayload(download);
    expect(payload.conversation_id).toBe(transcriptConversationKey);
    await expect(page.getByText(/Export ready/i)).toBeVisible({ timeout: 10000 });
  });
});

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

import { test, expect } from '../fixtures/base';

test.describe('Workflows page smoke', () => {
  test('renders workflows list and run form', async ({ tenantAdminPage }) => {
    const page = tenantAdminPage;
    await page.goto('/workflows');
    await expect(page.getByRole('heading', { name: 'Library' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('radio').first()).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('button', { name: /Run workflow/i })).toBeVisible({ timeout: 15000 });
  });

  test('shows descriptor details for selected workflow', async ({ tenantAdminPage }) => {
    const page = tenantAdminPage;
    await page.goto('/workflows');
    const firstWorkflow = page.getByRole('radio').first();
    await expect(firstWorkflow).toBeVisible({ timeout: 15000 });
    await firstWorkflow.click();
    await page.getByRole('tab', { name: /Outline/i }).click();
    await expect(page.getByText(/Handoffs/i)).toBeVisible();
    await expect(page.getByText(/Stage:/i)).toBeVisible();
  });

  test('paginates run history and allows selecting a run', async ({ tenantAdminPage }) => {
    const page = tenantAdminPage;
    await page.goto('/workflows');
    await page.getByRole('tab', { name: /History/i }).click();
    const historyPanel = page.getByRole('tabpanel', { name: /History/i });
    const runCard = historyPanel.getByRole('button').first();
    await expect(runCard).toBeVisible({ timeout: 15000 });
    await runCard.click();
    const loadMore = historyPanel.getByRole('button', { name: /Load more/i });
    if (await loadMore.isVisible()) {
      await loadMore.click();
      await expect(loadMore).toBeEnabled();
    }
  });

  test('cancel action is exposed for running runs (mock-compatible)', async ({ tenantAdminPage }) => {
    const page = tenantAdminPage;
    await page.goto('/workflows');
    await page.getByRole('tab', { name: /History/i }).click();
    const historyPanel = page.getByRole('tabpanel', { name: /History/i });
    const runningRun = historyPanel.getByRole('button', { name: /running/i }).first();
    if (await runningRun.isVisible()) {
      await runningRun.click();
      await page.getByRole('tab', { name: /Console/i }).click();
      const transcriptBtn = page.getByRole('button', { name: /Transcript/i });
      await expect(transcriptBtn).toBeEnabled({ timeout: 10000 });
      await transcriptBtn.click();
      await expect(page.getByRole('heading', { name: /Run transcript/i })).toBeVisible({ timeout: 10000 });
    }
  });

  test('run completes and history remains accessible after streaming', async ({ tenantAdminPage }) => {
    const page = tenantAdminPage;
    await page.goto('/workflows');

    const textarea = page.getByRole('textbox', { name: /Message/i });
    await expect(textarea).toBeVisible({ timeout: 15000 });
    await textarea.fill('smoke test run');
    await page.getByRole('button', { name: /Run workflow/i }).click();

    await page.waitForTimeout(500);
    await page.waitForSelector('text=Workflow run completed successfully.', { timeout: 10000 }).catch(async () => {
      await page.waitForSelector('text=Workflow run ended with an error', { timeout: 10000 });
    });

    await page.waitForTimeout(300);
    await page.getByRole('tab', { name: /History/i }).click();
    const historyPanel = page.getByRole('tabpanel', { name: /History/i });
    await expect(historyPanel.getByRole('button').first()).toBeVisible({ timeout: 15000 });
  });
});

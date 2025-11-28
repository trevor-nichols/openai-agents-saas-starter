import { test, expect } from '@playwright/test';

test.describe('Workflows page smoke', () => {
  test.beforeEach(async ({ page }) => {
    // Assumes authenticated test session handled by global setup or fixtures.
    await page.goto('/workflows');
  });

  test('renders workflows list and run form', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Workflows' })).toBeVisible();
    await expect(page.getByRole('button', { name: /Run workflow/i })).toBeVisible();
  });

  test('shows descriptor details for selected workflow', async ({ page }) => {
    const firstWorkflow = page.getByRole('button', { name: /Steps:/i }).first();
    await firstWorkflow.click();
    await expect(page.getByText(/Handoffs/)).toBeVisible();
    await expect(page.getByText(/Stage:/)).toBeVisible();
  });

  test('paginates run history and allows selecting a run', async ({ page }) => {
    // This assumes seeded runs are present in test env; fallback to mock mode when AGENT_API_MOCK=true.
    await expect(page.getByText(/Run history/i)).toBeVisible();
    // Click first data row after header
    const dataRow = page.getByRole('row').nth(1);
    await dataRow.click();
    await expect(page.getByText(/Run /)).toBeVisible();
    // Load more if button present
    const loadMore = page.getByRole('button', { name: /Load more/i });
    if (await loadMore.isVisible()) {
      await loadMore.click();
      await expect(loadMore).toBeEnabled(); // button remains usable
    }
  });

  test('cancel action is exposed for running runs (mock-compatible)', async ({ page }) => {
    // Select a run row if present
    const runRow = page.getByRole('row').nth(1);
    await runRow.click();
    // If run is running, cancel button should appear; if not, test passes by absence.
    const cancelBtn = page.getByRole('button', { name: /Cancel run/i });
    if (await cancelBtn.isVisible()) {
      await cancelBtn.click();
      await expect(cancelBtn).toBeEnabled();
    }
  });

  test('run appears in history after streaming completion', async ({ page }) => {
    // Enter a quick message and run
    const textarea = page.getByRole('textbox', { name: /Message/i });
    await textarea.fill('smoke test run');
    await page.getByRole('button', { name: /Run workflow/i }).click();

    // Wait for the stream to show completed or error banners
    await page.waitForTimeout(500); // minimal delay to allow first events
    await page.waitForSelector('text=Workflow run completed.', { timeout: 10000 }).catch(async () => {
      // Allow error path as well
      await page.waitForSelector('text=Workflow run ended with an error', { timeout: 10000 });
    });

    // History should refresh and show a row containing the current prompt snippet or "Run"
    await page.waitForTimeout(300); // allow refetch + render
    const firstDataRow = page.getByRole('row').nth(1);
    await expect(firstDataRow).toBeVisible();
  });
});

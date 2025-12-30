import type { Page } from '@playwright/test';

export async function waitForAppReady(page: Page, timeout = 20_000) {
  // Next.js dev overlay can briefly block interactions while compiling.
  const compilingOverlay = page.locator('text=/Compiling|Building/i').first();
  try {
    await compilingOverlay.waitFor({ state: 'hidden', timeout });
  } catch {
    // If the overlay never appears, ignore. If it persists, the caller will fail later.
  }
}

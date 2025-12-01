import { describe, expect, it, vi, beforeEach } from 'vitest';
import type { AppNavItem } from '@/components/shell/AppNavLinks';

describe('App layout navigation guards', () => {
  beforeEach(() => {
    vi.resetModules();
    delete process.env.NEXT_PUBLIC_ENABLE_BILLING;
  });

  it(
    'omits Billing nav when billing is disabled',
    { timeout: 10_000 },
    async () => {
    process.env.NEXT_PUBLIC_ENABLE_BILLING = 'false';
  const { buildPrimaryNav } = await import('../nav');

    const nav: AppNavItem[] = await buildPrimaryNav();
    expect(nav.some((item) => item.href === '/billing')).toBe(false);
    },
  );

  it(
    'includes Billing nav when billing is enabled',
    { timeout: 10_000 },
    async () => {
    process.env.NEXT_PUBLIC_ENABLE_BILLING = 'true';
  const { buildPrimaryNav } = await import('../nav');

    const nav: AppNavItem[] = await buildPrimaryNav();
    expect(nav.some((item) => item.href === '/billing')).toBe(true);
    },
  );
});

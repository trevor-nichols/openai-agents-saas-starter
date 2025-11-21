import { describe, expect, it, vi, beforeEach } from 'vitest';

describe('App layout navigation guards', () => {
  beforeEach(() => {
    vi.resetModules();
    delete process.env.NEXT_PUBLIC_ENABLE_BILLING;
  });

  it('omits Billing nav when billing is disabled', async () => {
    process.env.NEXT_PUBLIC_ENABLE_BILLING = 'false';
    const { buildPrimaryNav } = await import('./layout');

    const nav = buildPrimaryNav();
    expect(nav.some((item) => item.href === '/billing')).toBe(false);
  });

  it('includes Billing nav when billing is enabled', async () => {
    process.env.NEXT_PUBLIC_ENABLE_BILLING = 'true';
    const { buildPrimaryNav } = await import('./layout');

    const nav = buildPrimaryNav();
    expect(nav.some((item) => item.href === '/billing')).toBe(true);
  });
});

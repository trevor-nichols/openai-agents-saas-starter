import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AppNavItem } from '@/components/shell/AppNavLinks';

describe('App layout navigation guards', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it(
    'omits Billing nav when billing is disabled',
    { timeout: 10_000 },
    async () => {
      const { buildPrimaryNav } = await import('../nav');

      const nav: AppNavItem[] = buildPrimaryNav({ billingEnabled: false });
      expect(nav.some((item) => item.href === '/billing')).toBe(false);
    },
  );

  it(
    'includes Billing nav when billing is enabled',
    { timeout: 10_000 },
    async () => {
      const { buildPrimaryNav } = await import('../nav');

      const nav: AppNavItem[] = buildPrimaryNav({ billingEnabled: true });
      expect(nav.some((item) => item.href === '/billing')).toBe(true);
    },
  );

  it(
    'includes Storage under Workspace for tenant admins',
    { timeout: 10_000 },
    async () => {
      const { buildNavItems } = await import('../nav');

      const nav = buildNavItems({ hasStatusScope: false, hasOperator: false, role: 'admin' });
      const workspace = nav.find((item) => item.label === 'Workspace');
      const hasStorage = workspace?.items?.some((item) => item.href === '/ops/storage') ?? false;
      expect(hasStorage).toBe(true);
    },
  );

  it(
    'omits Storage under Workspace for non-admin roles',
    { timeout: 10_000 },
    async () => {
      const { buildNavItems } = await import('../nav');

      const nav = buildNavItems({ hasStatusScope: false, hasOperator: false, role: 'member' });
      const workspace = nav.find((item) => item.label === 'Workspace');
      const hasStorage = workspace?.items?.some((item) => item.href === '/ops/storage') ?? false;
      expect(hasStorage).toBe(false);
    },
  );

  it(
    'includes Storage under Workspace when admin scopes are present',
    { timeout: 10_000 },
    async () => {
      const { buildNavItems } = await import('../nav');

      const nav = buildNavItems({ hasStatusScope: false, hasOperator: false, scopes: ['billing:manage'] });
      const workspace = nav.find((item) => item.label === 'Workspace');
      const hasStorage = workspace?.items?.some((item) => item.href === '/ops/storage') ?? false;
      expect(hasStorage).toBe(true);
    },
  );
});

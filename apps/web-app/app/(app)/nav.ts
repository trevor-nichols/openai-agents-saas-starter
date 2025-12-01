import type { AppNavItem } from '@/components/shell/AppNavLinks';
import { billingEnabled } from '@/lib/config/features';

export async function buildPrimaryNav(): Promise<AppNavItem[]> {
  return [
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/chat', label: 'Workspace' },
    { href: '/workflows', label: 'Workflows' },
    { href: '/agents', label: 'Agents' },
    ...(billingEnabled ? [{ href: '/billing', label: 'Billing' }] : []),
  ];
}

export async function buildNavItems(hasStatusScope: boolean): Promise<AppNavItem[]> {
  const primaryNav = await buildPrimaryNav();
  if (!hasStatusScope) {
    return primaryNav;
  }

  const opsLinks: AppNavItem[] = [
    {
      href: '/ops/status',
      label: 'Ops',
      badge: 'Admin',
      badgeVariant: 'outline',
    },
    {
      href: '/ops/storage',
      label: 'Storage',
      badge: 'Admin',
      badgeVariant: 'outline',
    },
  ];

  return [...primaryNav, ...opsLinks];
}

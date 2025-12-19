import type { AppNavItem, NavIconKey } from '@/components/shell/AppNavLinks';
import { billingEnabled } from '@/lib/config/features';

const PRIMARY_NAV: AppNavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: 'layout-dashboard' satisfies NavIconKey },
  {
    href: '#',
    label: 'Workspace',
    icon: 'square-terminal' satisfies NavIconKey,
    items: [
      { href: '/chat', label: 'Chat' },
      { href: '/assets', label: 'Assets' },
      { href: '/workflows', label: 'Workflows' },
      { href: '/agents', label: 'Agents' },
    ],
  },
];

const BILLING_NAV: AppNavItem = {
  href: '/billing',
  label: 'Billing',
  icon: 'credit-card',
};

const OPS_NAV: AppNavItem[] = [
  {
    href: '/ops/status',
    label: 'Ops',
    badge: 'Admin',
    badgeVariant: 'outline',
    icon: 'activity',
  },
  {
    href: '/ops/storage',
    label: 'Storage',
    badge: 'Admin',
    badgeVariant: 'outline',
    icon: 'database',
  },
];

export function buildPrimaryNav(): AppNavItem[] {
  return billingEnabled ? [...PRIMARY_NAV, BILLING_NAV] : [...PRIMARY_NAV];
}

export function buildNavItems(hasStatusScope: boolean): AppNavItem[] {
  const primaryNav = buildPrimaryNav();
  if (!hasStatusScope) {
    return primaryNav;
  }

  return [...primaryNav, ...OPS_NAV];
}

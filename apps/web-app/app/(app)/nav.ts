import type { AppNavItem, NavIconKey } from '@/components/shell/AppNavLinks';
import { isTenantAdmin } from '@/lib/auth/roles';
import { billingEnabled } from '@/lib/config/features';

const STORAGE_NAV_ITEM: AppNavItem = {
  href: '/ops/storage',
  label: 'Storage',
  badge: 'Admin',
  badgeVariant: 'outline',
};

const WORKSPACE_CHAT_ITEM: AppNavItem = { href: '/chat', label: 'Chat' };
const WORKSPACE_ASSETS_ITEM: AppNavItem = { href: '/assets', label: 'Assets' };
const WORKSPACE_WORKFLOWS_ITEM: AppNavItem = { href: '/workflows', label: 'Workflows' };
const WORKSPACE_AGENTS_ITEM: AppNavItem = { href: '/agents', label: 'Agents' };

const WORKSPACE_BASE_ITEMS: AppNavItem[] = [
  WORKSPACE_CHAT_ITEM,
  WORKSPACE_ASSETS_ITEM,
  WORKSPACE_WORKFLOWS_ITEM,
  WORKSPACE_AGENTS_ITEM,
];

const WORKSPACE_ITEMS_WITH_STORAGE: AppNavItem[] = [
  WORKSPACE_CHAT_ITEM,
  WORKSPACE_ASSETS_ITEM,
  STORAGE_NAV_ITEM,
  WORKSPACE_WORKFLOWS_ITEM,
  WORKSPACE_AGENTS_ITEM,
];

const PRIMARY_NAV: AppNavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: 'layout-dashboard' satisfies NavIconKey },
  {
    href: '#',
    label: 'Workspace',
    icon: 'square-terminal' satisfies NavIconKey,
    items: WORKSPACE_BASE_ITEMS,
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
];

export function buildPrimaryNav({ includeStorage = false }: { includeStorage?: boolean } = {}): AppNavItem[] {
  const workspaceItems = includeStorage ? WORKSPACE_ITEMS_WITH_STORAGE : WORKSPACE_BASE_ITEMS;

  const primary = PRIMARY_NAV.map((item) =>
    item.label === 'Workspace' ? { ...item, items: workspaceItems } : item,
  );

  return billingEnabled ? [...primary, BILLING_NAV] : [...primary];
}

export function buildNavItems({
  hasStatusScope,
  role,
  scopes,
}: {
  hasStatusScope: boolean;
  role?: string | null;
  scopes?: string[] | null;
}): AppNavItem[] {
  const primaryNav = buildPrimaryNav({
    includeStorage: isTenantAdmin({ role, scopes }),
  });
  if (!hasStatusScope) {
    return primaryNav;
  }

  return [...primaryNav, ...OPS_NAV];
}

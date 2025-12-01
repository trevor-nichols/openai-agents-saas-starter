import {
  Activity,
  Bot,
  CreditCard,
  Database,
  LayoutDashboard,
  MessageSquare,
  Workflow,
} from 'lucide-react';

import type { AppNavItem } from '@/components/shell/AppNavLinks';
import { billingEnabled } from '@/lib/config/features';

export async function buildPrimaryNav(): Promise<AppNavItem[]> {
  return [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/chat', label: 'Workspace', icon: MessageSquare },
    { href: '/workflows', label: 'Workflows', icon: Workflow },
    { href: '/agents', label: 'Agents', icon: Bot },
    ...(billingEnabled ? [{ href: '/billing', label: 'Billing', icon: CreditCard }] : []),
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
      icon: Activity,
    },
    {
      href: '/ops/storage',
      label: 'Storage',
      badge: 'Admin',
      badgeVariant: 'outline',
      icon: Database,
    },
  ];

  return [...primaryNav, ...opsLinks];
}

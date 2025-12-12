import type { AppNavItem } from '@/components/shell/AppNavLinks';
import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { billingEnabled } from '@/lib/config/features';

import { buildNavItems } from '../nav';

export const ACCOUNT_NAV: AppNavItem[] = [
  { href: '/account', label: 'Account' },
  { href: '/settings/access', label: 'Signup guardrails' },
  { href: '/settings/tenant', label: 'Tenant settings' },
];

export async function getAppShellLayoutModel(): Promise<{
  session: Awaited<ReturnType<typeof getSessionMetaFromCookies>>;
  navItems: AppNavItem[];
  accountNav: AppNavItem[];
  subtitle: string;
}> {
  const session = await getSessionMetaFromCookies();
  const hasStatusScope = session?.scopes?.includes('status:manage') ?? false;
  const navItems = buildNavItems(hasStatusScope);

  const subtitle = billingEnabled
    ? 'Configure agents, monitor conversations, and keep billing healthy.'
    : 'Configure agents and monitor conversations.';

  return { session, navItems, accountNav: ACCOUNT_NAV, subtitle };
}


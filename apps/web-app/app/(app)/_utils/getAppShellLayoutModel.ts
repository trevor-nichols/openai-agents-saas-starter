import type { AppNavItem } from '@/components/shell/AppNavLinks';
import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { billingEnabled } from '@/lib/config/features';
import { getCurrentUserProfile } from '@/lib/server/services/users';

import { buildNavItems } from '../nav';

export const ACCOUNT_NAV: AppNavItem[] = [
  { href: '/account', label: 'Account' },
  { href: '/settings/team', label: 'Team' },
  { href: '/settings/access', label: 'Signup guardrails' },
  { href: '/settings/tenant', label: 'Tenant settings' },
];

export async function getAppShellLayoutModel(): Promise<{
  session: Awaited<ReturnType<typeof getSessionMetaFromCookies>>;
  navItems: AppNavItem[];
  accountNav: AppNavItem[];
  subtitle: string;
  profile: Awaited<ReturnType<typeof getCurrentUserProfile>> | null;
}> {
  const session = await getSessionMetaFromCookies();
  let profile: Awaited<ReturnType<typeof getCurrentUserProfile>> | null = null;
  if (session) {
    try {
      profile = await getCurrentUserProfile();
    } catch (error) {
      console.warn('[app-shell] Failed to load current user profile', error);
    }
  }

  const hasStatusScope = session?.scopes?.includes('status:manage') ?? false;
  const navItems = buildNavItems({
    hasStatusScope,
    role: profile?.role ?? null,
    scopes: session?.scopes ?? null,
  });

  const subtitle = billingEnabled
    ? 'Configure agents, monitor conversations, and keep billing healthy.'
    : 'Configure agents and monitor conversations.';

  return { session, navItems, accountNav: ACCOUNT_NAV, subtitle, profile };
}

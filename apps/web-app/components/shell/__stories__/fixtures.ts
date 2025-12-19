import type { AppNavItem } from '../AppNavLinks';
import type { ActivityEvent } from '@/types/activity';

export const shellNavItems: AppNavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: 'layout-dashboard' },
  { href: '/chat', label: 'Workspace', icon: 'message-square', badge: 'Live', badgeVariant: 'secondary' },
  { href: '/workflows', label: 'Workflows', icon: 'workflow' },
  { href: '/agents', label: 'Agents', icon: 'bot' },
  { href: '/billing', label: 'Billing', icon: 'credit-card', badge: 'Pro', badgeVariant: 'outline' },
];

export const shellAccountItems: AppNavItem[] = [
  { href: '/account', label: 'Account', icon: 'layout-dashboard' },
  { href: '/settings/access', label: 'Access', icon: 'activity', badge: 'New' },
  { href: '/ops/status', label: 'Ops', icon: 'database', badge: 'Admin', badgeVariant: 'outline' },
];

export const shellUser = {
  name: 'Ava Agent',
  email: 'ava@acme.ai',
  tenantId: 'acme-t1',
  avatarUrl: 'https://avatars.githubusercontent.com/u/63446714?v=4',
};

const now = Date.now();

export const shellActivityEvents: ActivityEvent[] = [
  {
    id: 'evt-1',
    tenant_id: 'acme-t1',
    action: 'billing.invoice.created',
    status: 'success',
    created_at: new Date(now - 15 * 60 * 1000).toISOString(),
    object_type: 'Invoice',
    object_id: 'INV-2045',
    metadata: { amount: '$120.00', plan: 'Pro' },
    read_state: 'unread',
  },
  {
    id: 'evt-2',
    tenant_id: 'acme-t1',
    action: 'agents.workflow.run_failed',
    status: 'failure',
    created_at: new Date(now - 2 * 60 * 60 * 1000).toISOString(),
    object_type: 'Workflow Run',
    object_id: 'run_87344',
    metadata: { step: 'billing-retry', error: 'Rate limit' },
    read_state: 'unread',
  },
  {
    id: 'evt-3',
    tenant_id: 'acme-t1',
    action: 'auth.session.issued',
    status: 'pending',
    created_at: new Date(now - 6 * 60 * 60 * 1000).toISOString(),
    object_type: 'Session',
    object_id: 'sess_44de',
    metadata: { ip: '192.0.2.12', agent: 'Chrome' },
    read_state: 'read',
  },
];

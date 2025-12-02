import type { QuickAction } from './types';
import { Bot, MessageSquare, ShieldCheck, Sparkles, WalletMinimal } from 'lucide-react';

export const DASHBOARD_COPY = {
  header: {
    eyebrow: 'Overview',
    title: 'Command center',
    description: 'Monitor agents, activity, and billing health from a single glass surface.',
    ctaLabel: 'New chat',
  },
  billingPreview: {
    eyebrow: 'Billing',
    title: 'Plan overview',
    description: 'Live subscription state streamed from Stripe.',
    ctaLabel: 'Manage plan',
    emptyEvents: 'Usage, invoices, and subscription updates will land here once activity starts.',
  },
  activityFeed: {
    title: 'Recent activity',
    description: 'Tenant-scoped audit log across auth, workflows, billing, and storage.',
    emptyTitle: 'No activity yet',
    emptyDescription: 'Actions across your tenant will appear here as they happen.',
  },
};

export const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'start-chat',
    label: 'Open chat workspace',
    description: 'Jump into the full-screen workspace to collaborate with your agents.',
    href: '/chat',
    icon: MessageSquare,
  },
  {
    id: 'register-agent',
    label: 'Register a new agent',
    description: 'Provision a service account and configure a new GPT-5 agent persona.',
    href: '/agents',
    icon: Bot,
  },
  {
    id: 'review-billing',
    label: 'Review billing usage',
    description: 'Track plan status, invoices, and usage events in real time.',
    href: '/billing',
    icon: WalletMinimal,
  },
  {
    id: 'harden-security',
    label: 'Review security posture',
    description: 'Rotate service-account keys and audit login sessions.',
    href: '/account/security',
    icon: ShieldCheck,
  },
  {
    id: 'explore-tools',
    label: 'Explore tool catalog',
    description: 'Pair your agents with first-party and custom billing-aware tools.',
    href: '/agents',
    icon: Sparkles,
  },
];

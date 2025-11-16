export type MarketingNavLink = {
  label: string;
  href: string;
  description: string;
  badge?: string;
};

export const MARKETING_PRIMARY_LINKS: MarketingNavLink[] = [
  {
    label: 'Features',
    href: '/features',
    description: 'Deep dive into the agent workspace, billing, and observability flows.',
  },
  {
    label: 'Pricing',
    href: '/pricing',
    description: 'Compare starter and scale plans with live usage data pulled from the billing hub.',
  },
  {
    label: 'Docs',
    href: '/docs',
    description: 'Implementation guides, API references, and setup checklists for this starter.',
    badge: 'New',
  },
];

export const MARKETING_SECONDARY_LINKS: MarketingNavLink[] = [
  {
    label: 'Login',
    href: '/login',
    description: 'Access the operator console to manage tenants and agents.',
  },
  {
    label: 'Request access',
    href: '/request-access',
    description: 'Submit your use case to receive an invite token when approvals open.',
  },
];

export const MARKETING_CTA_LINK: MarketingNavLink = {
  label: 'Get started',
  href: '/register',
  description: 'Create an account and clone the repo in minutes.',
  badge: 'Live data',
};

export const MARKETING_ANNOUNCEMENT = {
  tag: 'Update',
  message: 'Agents SDK v0.5 is fully wired into the starter.',
  href: '/docs',
};

export const MARKETING_FOOTER_COLUMNS = [
  {
    title: 'Product',
    links: [
      { label: 'Overview', href: '/' },
      { label: 'Chat workspace', href: '/chat' },
      { label: 'Billing hub', href: '/billing' },
      { label: 'Security center', href: '/account/security' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { label: 'Docs', href: '/docs' },
      { label: 'Agents SDK guide', href: '/docs#agents' },
      { label: 'Pricing', href: '/pricing' },
      { label: 'Status', href: '/status' },
    ],
  },
  {
    title: 'Company',
    links: [
      { label: 'About', href: '/features' },
      { label: 'Contact', href: '/contact' },
      { label: 'Privacy', href: '/privacy' },
      { label: 'Terms', href: '/terms' },
    ],
  },
];

export const MARKETING_SOCIAL_LINKS = [
  { label: 'GitHub', href: 'https://github.com/openai', external: true },
  { label: 'Status', href: '/status' },
  { label: 'Changelog', href: '/docs#changelog' },
];

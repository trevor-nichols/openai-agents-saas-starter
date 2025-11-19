export const ACCOUNT_TABS = [
  { key: 'profile', label: 'Profile' },
  { key: 'security', label: 'Security' },
  { key: 'sessions', label: 'Sessions' },
  { key: 'automation', label: 'Automation' },
] as const;

export const ACCOUNT_COPY = {
  header: {
    eyebrow: 'Account',
    title: 'Manage your workspace profile',
    description: 'Update profile metadata, tighten security controls, and review session activity in one place.',
    ctaLabel: 'Billing settings',
  },
  emptyServiceAccount: {
    title: 'No service accounts',
    description: 'Create automation credentials to integrate with external systems.',
  },
};

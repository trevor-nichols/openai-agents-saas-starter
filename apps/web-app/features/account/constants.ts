export const ACCOUNT_TABS = [
  { key: 'profile', label: 'Profile', helper: 'Identity & tenant' },
  { key: 'security', label: 'Security', helper: 'Password & MFA' },
  { key: 'sessions', label: 'Sessions', helper: 'Devices & activity' },
  { key: 'automation', label: 'Automation', helper: 'Service accounts' },
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

export const SERVICE_ACCOUNTS_DOC_URL =
  'https://github.com/openai/openai-agents-saas-starter/blob/main/docs/frontend/features/account-service-accounts.md';

export const PROFILE_FIELD_LIMITS = {
  displayName: 128,
  givenName: 64,
  familyName: 64,
  avatarUrl: 512,
  timezone: 64,
  locale: 32,
} as const;

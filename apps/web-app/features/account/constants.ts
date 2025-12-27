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

export const PASSWORD_POLICY_RULES = [
  '14+ characters with upper, lower, number, and symbol.',
  'No reuse of the last 5 passwords.',
  'Strength score ≥3 enforced by the backend policy engine.',
] as const;

export const MAX_BILLING_CONTACTS = 10;

export const FLAG_PRESETS = [
  {
    key: 'beta_features',
    label: 'Enable beta features',
    description: 'Allow this tenant to try experimental UI and agent capabilities before launch.',
  },
  {
    key: 'require_mfa',
    label: 'Require MFA',
    description: 'Force all members to enroll in multi-factor auth before performing admin actions.',
  },
  {
    key: 'sandbox_mode',
    label: 'Sandbox mode',
    description: 'Route conversations and billing to sandbox integrations for test tenants.',
  },
  {
    key: 'usage_alerts',
    label: 'Usage alerts',
    description: 'Email billing contacts when usage crosses 70% and 95% of plan limits.',
  },
] as const;

export function useSignupCtaTarget() {
  return {
    policy: 'public',
    cta: { label: 'Create an account', href: '/register', intent: 'primary' },
    isLoading: false,
    requiresInviteToken: false,
  };
}

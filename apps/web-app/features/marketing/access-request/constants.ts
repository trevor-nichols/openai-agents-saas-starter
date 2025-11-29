import type { SignupAccessPolicyMode } from '@/types/signup';

export const ACCESS_REQUEST_COPY = {
  eyebrow: 'Invite-only access',
  title: 'Request an operator review for your deployment.',
  description:
    'Tell us about your use case and we will review the request before provisioning an invite token. Operators typically respond within one business day.',
  talkingPoints: [
    'SOC 2-ready auth, billing, and observability land in every tenant.',
    'Invites prevent list stuffing and ensure rollout compliance.',
    'Approvals log structured metadata for audit reviews.',
  ],
} as const;

export const SUCCESS_COPY: Record<SignupAccessPolicyMode, { title: string; body: string }> = {
  public: {
    title: 'Request received',
    body: 'We still logged your note and will follow up, but you can create an account immediately while we review.',
  },
  invite_only: {
    title: 'Request submitted',
    body: 'Operators will validate the details and send an invite token to your inbox once approved.',
  },
  approval: {
    title: 'Under review',
    body: 'Approvals typically take one business day. When approved you will receive an invite token with next steps.',
  },
};

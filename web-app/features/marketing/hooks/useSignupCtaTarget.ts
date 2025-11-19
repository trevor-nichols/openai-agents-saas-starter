'use client';

import { useMemo } from 'react';

import { useSignupPolicyQuery } from '@/lib/queries/signup';
import { resolveSignupPolicyMode, type SignupAccessPolicyMode } from '@/types/signup';

import type { CtaLink } from '../types';

const CTA_BY_POLICY: Record<SignupAccessPolicyMode, CtaLink> = {
  public: {
    label: 'Create an account',
    href: '/register',
    intent: 'primary',
  },
  invite_only: {
    label: 'Request access',
    href: '/request-access',
    intent: 'primary',
  },
  approval: {
    label: 'Request access',
    href: '/request-access',
    intent: 'primary',
  },
};

export function useSignupCtaTarget() {
  const { data, isLoading } = useSignupPolicyQuery();
  const policyMode = resolveSignupPolicyMode(data);

  const cta = useMemo(() => CTA_BY_POLICY[policyMode] ?? CTA_BY_POLICY.public, [policyMode]);

  return {
    policy: policyMode,
    cta,
    isLoading,
    requiresInviteToken: policyMode !== 'public',
  };
}

'use client';

import { useCallback } from 'react';

import { trackEvent } from '@/lib/analytics';
import type { CtaLink } from '../types';

interface CtaEventMeta {
  location: string;
  cta: CtaLink;
}

export function useMarketingAnalytics() {
  const trackCtaClick = useCallback((meta: CtaEventMeta) => {
    trackEvent({
      event: 'marketing_cta_clicked',
      channel: 'marketing',
      location: meta.location,
      metadata: {
        label: meta.cta.label,
        href: meta.cta.href,
        intent: meta.cta.intent,
      },
    });
  }, []);

  const trackLeadSubmit = useCallback((payload: {
    location: string;
    channel: 'email' | 'webhook';
    severity: string;
    emailDomain?: string;
  }) => {
    trackEvent({
      event: 'marketing_lead_submitted',
      channel: 'marketing',
      location: payload.location,
      metadata: {
        channel: payload.channel,
        severity: payload.severity,
        emailDomain: payload.emailDomain,
      },
    });
  }, []);

  return {
    trackCtaClick,
    trackLeadSubmit,
  };
}

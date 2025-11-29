'use client';

import { useState } from 'react';

import { GlassPanel } from '@/components/ui/foundation';
import { useMarketingAnalytics } from '@/features/marketing/hooks/useMarketingAnalytics';

import { AccessRequestHero } from './components/AccessRequestHero';
import { AccessRequestForm } from './components/AccessRequestForm';
import { SubmissionSuccess } from './components/SubmissionSuccess';
import type { AccessRequestSubmission } from './types';

export function AccessRequestExperience() {
  const [submission, setSubmission] = useState<AccessRequestSubmission | null>(null);
  const { trackLeadSubmit } = useMarketingAnalytics();

  const handleSubmitted = (payload: AccessRequestSubmission) => {
    setSubmission(payload);
    const [, domain] = payload.email.split('@');
    trackLeadSubmit({
      location: 'access-request:submit',
      channel: 'email',
      severity: 'informational',
      emailDomain: domain?.toLowerCase(),
    });
  };

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-10 px-6 py-16">
      <AccessRequestHero />
      <GlassPanel className="p-8">
        {submission ? (
          <SubmissionSuccess submission={submission} onReset={() => setSubmission(null)} />
        ) : (
          <AccessRequestForm onSubmitted={handleSubmitted} />
        )}
      </GlassPanel>
    </div>
  );
}

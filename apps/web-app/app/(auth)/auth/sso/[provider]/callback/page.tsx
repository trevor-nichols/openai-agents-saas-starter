import { Suspense } from 'react';
import type { Metadata } from 'next';

import { AuthCard } from '@/app/(auth)/_components/AuthCard';
import { SsoCallbackClient } from '@/components/auth/SsoCallbackClient';

export const metadata: Metadata = {
  title: 'Completing sign in · Acme',
  description: 'Finalizing your single sign-on session.',
};

interface SsoCallbackPageProps {
  params: Promise<{ provider: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default function SsoCallbackPage({ params, searchParams }: SsoCallbackPageProps) {
  return (
    <Suspense fallback={null}>
      <SsoCallbackContent params={params} searchParams={searchParams} />
    </Suspense>
  );
}

async function SsoCallbackContent({ params, searchParams }: SsoCallbackPageProps) {
  const { provider } = await params;
  const query = await searchParams;

  const code = typeof query.code === 'string' ? query.code : null;
  const state = typeof query.state === 'string' ? query.state : null;
  const error = typeof query.error === 'string' ? query.error : null;
  const errorDescription =
    typeof query.error_description === 'string' ? query.error_description : null;

  return (
    <AuthCard
      title="Finalizing your sign-in"
      description="Hang tight while we connect your account."
      badge="Single sign-on"
    >
      <SsoCallbackClient
        provider={provider}
        code={code}
        state={state}
        error={error}
        errorDescription={errorDescription}
      />
    </AuthCard>
  );
}

import type { Metadata } from 'next';

import { Suspense } from 'react';

import { AuthCard } from '@/app/(auth)/_components/AuthCard';
import { VerifyEmailClient } from '@/app/(auth)/email/verify/VerifyEmailClient';

interface VerifyEmailPageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export const metadata: Metadata = {
  title: 'Verify email · Acme',
  description: 'Confirm your email address to finish setting up your Acme workspace.',
};

export default async function VerifyEmailPage({ searchParams }: VerifyEmailPageProps) {
  const params = await searchParams;
  const token = typeof params?.token === 'string' ? params.token : undefined;

  return (
    <Suspense fallback={null}>
      <VerifyEmailContent token={token} />
    </Suspense>
  );
}

function VerifyEmailContent({ token }: { token?: string }) {
  return (
    <AuthCard
      title="Verify your email address"
      description="Resend the verification link or paste the token from your email to finish onboarding."
    >
      <VerifyEmailClient token={token} />
    </AuthCard>
  );
}

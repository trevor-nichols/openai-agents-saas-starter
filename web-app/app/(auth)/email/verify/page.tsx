import type { Metadata } from 'next';

import { AuthCard } from '@/app/(auth)/_components/AuthCard';
import { VerifyEmailClient } from '@/app/(auth)/email/verify/VerifyEmailClient';

interface VerifyEmailPageProps {
  searchParams?: Record<string, string | string[] | undefined>;
}

export const metadata: Metadata = {
  title: 'Verify email · Acme',
  description: 'Confirm your email address to finish setting up your Acme workspace.',
};

export default function VerifyEmailPage({ searchParams }: VerifyEmailPageProps) {
  const token = typeof searchParams?.token === 'string' ? searchParams.token : undefined;

  return (
    <AuthCard
      title="Verify your email address"
      description="Resend the verification link or paste the token from your email to finish onboarding."
    >
      <VerifyEmailClient token={token} />
    </AuthCard>
  );
}

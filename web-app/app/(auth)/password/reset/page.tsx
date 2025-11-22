import type { Metadata } from 'next';
import Link from 'next/link';

import { Suspense } from 'react';

import { AuthCard } from '@/app/(auth)/_components/AuthCard';
import { ResetPasswordForm } from '@/components/auth/ResetPasswordForm';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface ResetPasswordPageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export const metadata: Metadata = {
  title: 'Reset password · Acme',
  description: 'Choose a new password to secure your Acme account.',
};

export default async function ResetPasswordPage({ searchParams }: ResetPasswordPageProps) {
  const params = await searchParams;
  const token = typeof params?.token === 'string' ? params.token : undefined;

  return (
    <Suspense fallback={null}>
      <ResetPasswordContent token={token} />
    </Suspense>
  );
}

function ResetPasswordContent({ token }: { token?: string }) {
  return (
    <AuthCard
      title="Reset your password"
      description="Choose a new password to secure your account."
      footer={
        <p className="text-center text-sm text-muted-foreground">
          Ready to sign in?{' '}
          <Link href="/login" className="font-medium text-primary hover:underline">
            Return to login
          </Link>
        </p>
      }
    >
      {token ? (
        <ResetPasswordForm token={token} />
      ) : (
        <Alert variant="destructive">
          <AlertTitle>Reset link missing</AlertTitle>
          <AlertDescription>
            We couldn&apos;t find a valid reset token in the URL. Please open the password reset link from your email or
            request a new one.
          </AlertDescription>
        </Alert>
      )}
    </AuthCard>
  );
}

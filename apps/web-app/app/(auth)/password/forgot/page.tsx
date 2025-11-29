import type { Metadata } from 'next';
import Link from 'next/link';

import { AuthCard } from '@/app/(auth)/_components/AuthCard';
import { ForgotPasswordForm } from '@/components/auth/ForgotPasswordForm';

export const metadata: Metadata = {
  title: 'Forgot password · Acme',
  description: 'Request a secure password reset link for your Acme account.',
};

export default function ForgotPasswordPage() {
  return (
    <AuthCard
      title="Forgot your password?"
      description="We’ll send you a secure reset link so you can get back into your workspace."
      footer={
        <p className="text-center text-sm text-muted-foreground">
          Remember it again?{' '}
          <Link href="/login" className="font-medium text-primary hover:underline">
            Back to login
          </Link>
        </p>
      }
    >
      <ForgotPasswordForm />
    </AuthCard>
  );
}

import { Suspense } from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';

import { AuthCard } from '@/app/(auth)/_components/AuthCard';
import { LoginForm } from '@/components/auth/LoginForm';

export const metadata: Metadata = {
  title: 'Sign in · Acme',
  description: 'Access your Acme workspace with your organization credentials.',
};

interface LoginPageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default function LoginPage({ searchParams }: LoginPageProps) {
  return (
    <Suspense fallback={null}>
      <LoginPageContent searchParams={searchParams} />
    </Suspense>
  );
}

async function LoginPageContent({ searchParams }: LoginPageProps) {
  const params = await searchParams;
  const redirectParam = typeof params?.redirectTo === 'string' ? params.redirectTo : undefined;
  const redirectTo = redirectParam && redirectParam.startsWith('/') ? redirectParam : undefined;

  return (
    <AuthCard
      title="Sign in to Acme"
      description="Use your organization credentials to continue."
      footer={
        <div className="flex flex-col gap-2 text-center sm:flex-row sm:items-center sm:justify-between sm:text-left">
          <p>
            New here?{' '}
            <Link href="/register" className="font-medium text-primary hover:underline">
              Create an account
            </Link>
          </p>
          <Link href="/password/forgot" className="text-sm text-muted-foreground hover:text-foreground">
            Forgot password
          </Link>
        </div>
      }
    >
      <LoginForm redirectTo={redirectTo} />
    </AuthCard>
  );
}

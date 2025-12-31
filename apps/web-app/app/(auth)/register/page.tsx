import type { Metadata } from 'next';
import Link from 'next/link';
import { connection } from 'next/server';

import { AuthCard } from '@/app/(auth)/_components/AuthCard';
import { RegisterForm } from '@/components/auth/RegisterForm';
import { getSignupAccessPolicy } from '@/lib/server/services/auth/signupGuardrails';
import type { SignupAccessPolicy } from '@/types/signup';

export const metadata: Metadata = {
  title: 'Create account · Acme',
  description: 'Provision a new tenant and admin account to start building with Acme.',
};

export default async function RegisterPage() {
  await connection();
  let policy: SignupAccessPolicy | null = null;

  try {
    policy = await getSignupAccessPolicy();
  } catch (error) {
    console.error('Unable to load signup policy for register page.', error);
  }

  return (
    <AuthCard
      title="Create your Acme account"
      description="Provision a tenant and admin account in a single step."
      footer={
        <p className="text-center">
          Already have access?{' '}
          <Link href="/login" className="font-medium text-primary hover:underline">
            Return to login
          </Link>
        </p>
      }
    >
      <RegisterForm policy={policy} requestAccessHref="/request-access" />
    </AuthCard>
  );
}

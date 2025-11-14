import type { Metadata } from 'next';
import Link from 'next/link';

import { AuthCard } from '@/app/(auth)/_components/AuthCard';
import { RegisterForm } from '@/components/auth/RegisterForm';

export const metadata: Metadata = {
  title: 'Create account · Anything Agents',
  description: 'Provision a new tenant and admin account to start building with Anything Agents.',
};

export default function RegisterPage() {
  return (
    <AuthCard
      title="Create your Anything Agents account"
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
      <RegisterForm />
    </AuthCard>
  );
}

import { redirect } from 'next/navigation';

import { Suspense } from 'react';

import { SignupGuardrailsWorkspace } from '@/features/settings';
import { getSessionMetaFromCookies } from '@/lib/auth/cookies';

export const metadata = {
  title: 'Signup Guardrails | Acme',
};

export default function SignupGuardrailsPage() {
  return (
    <Suspense fallback={null}>
      <SignupGuardrailsContent />
    </Suspense>
  );
}

async function SignupGuardrailsContent() {
  const session = await getSessionMetaFromCookies();
  const scopes = session?.scopes ?? [];
  const canManageAuth = scopes.includes('auth:manage') || scopes.includes('platform:admin');

  if (!session?.tenantId || !canManageAuth) {
    redirect('/dashboard');
  }

  return <SignupGuardrailsWorkspace />;
}

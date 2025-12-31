import type { Metadata } from 'next';
import { Suspense } from 'react';

import { AuthCard } from '@/app/(auth)/_components/AuthCard';
import { AcceptInviteForm } from '@/components/auth/AcceptInviteForm';
import { getSessionMetaFromCookies } from '@/lib/auth/cookies';

export const metadata: Metadata = {
  title: 'Accept invite · Acme',
  description: 'Join your workspace and set your password.',
};

interface AcceptInvitePageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default function AcceptInvitePage({ searchParams }: AcceptInvitePageProps) {
  return (
    <Suspense fallback={null}>
      <AcceptInviteContent searchParams={searchParams} />
    </Suspense>
  );
}

async function AcceptInviteContent({ searchParams }: AcceptInvitePageProps) {
  const params = await searchParams;
  const token = typeof params?.token === 'string' ? params.token : '';
  const session = await getSessionMetaFromCookies();

  return (
    <AuthCard
      title="Accept your invite"
      description="Set your password and join the tenant workspace."
    >
      <AcceptInviteForm initialToken={token} canAcceptExisting={Boolean(session)} />
    </AuthCard>
  );
}

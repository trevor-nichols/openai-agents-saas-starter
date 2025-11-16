'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { SectionHeader } from '@/components/ui/foundation';
import { useSignupPolicyQuery } from '@/lib/queries/signup';

import { PolicyBanner } from './components/PolicyBanner';
import { InvitesPanel } from './components/InvitesPanel';
import { RequestsPanel } from './components/RequestsPanel';

export function SignupGuardrailsWorkspace() {
  const { data: policy, isLoading, error, refetch } = useSignupPolicyQuery();

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow="Signup Guardrails"
        title="Manage invites and approvals"
        description="Issue invite tokens, review access requests, and monitor the policy that governs public signup."
      />

      <PolicyBanner policy={policy} isLoading={isLoading} error={error?.message} onRetry={() => refetch()} />

      <Tabs defaultValue="invites" className="space-y-6">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="invites">Invites</TabsTrigger>
          <TabsTrigger value="requests">Requests</TabsTrigger>
        </TabsList>

        <TabsContent value="invites">
          <InvitesPanel />
        </TabsContent>

        <TabsContent value="requests">
          <RequestsPanel />
        </TabsContent>
      </Tabs>
    </section>
  );
}

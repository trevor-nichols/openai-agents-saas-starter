import { Suspense } from 'react';

import { TenantOpsWorkspace } from '@/features/tenant-ops';
import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { hasOperatorScope } from '@/lib/auth/roles';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';

export default function TenantOpsPage() {
  return (
    <Suspense fallback={null}>
      <TenantOpsContent />
    </Suspense>
  );
}

async function TenantOpsContent() {
  const session = await getSessionMetaFromCookies();
  const canOperate = hasOperatorScope(session?.scopes ?? null);

  if (!canOperate) {
    return (
      <section className="space-y-6">
        <SectionHeader
          eyebrow="Operations"
          title="Tenant operations"
          description="Review tenant lifecycle status and manage platform access."
        />

        <GlassPanel className="space-y-2 border border-warning/40 bg-warning/5">
          <p className="text-base font-semibold text-foreground">Operator scope required</p>
          <p className="text-sm text-foreground/70">
            You need the <span className="font-semibold">platform:operator</span> or <span className="font-semibold">support:*</span> scope
            to access tenant lifecycle tooling. Ask an administrator to grant access, then refresh this page.
          </p>
        </GlassPanel>
      </section>
    );
  }

  return <TenantOpsWorkspace />;
}

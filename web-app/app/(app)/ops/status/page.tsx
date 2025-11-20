import { StatusOpsWorkspace } from '@/features/status-ops';
import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';

export default async function StatusOpsPage() {
  const session = await getSessionMetaFromCookies();
  const hasStatusScope = session?.scopes?.includes('status:manage') ?? false;

  if (!hasStatusScope) {
    return (
      <section className="space-y-6">
        <SectionHeader
          eyebrow="Operations"
          title="Status console"
          description="Audit status alert subscribers and replay incident notifications."
        />

        <GlassPanel className="space-y-2 border border-warning/40 bg-warning/5">
          <p className="text-base font-semibold text-foreground">Operator scope required</p>
          <p className="text-sm text-foreground/70">
            You need the <span className="font-semibold">status:manage</span> scope to access the status operator console.
            Ask an administrator to grant the scope, then refresh this page.
          </p>
        </GlassPanel>
      </section>
    );
  }

  return <StatusOpsWorkspace defaultTenantId={session?.tenantId ?? null} />;
}

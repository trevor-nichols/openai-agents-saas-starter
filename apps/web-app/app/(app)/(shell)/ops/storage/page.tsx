import { Suspense } from 'react';

import { StorageAdmin } from '@/features/storage/StorageAdmin';
import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { isTenantAdmin } from '@/lib/auth/roles';
import { getCurrentUserProfile } from '@/lib/server/services/users';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';

export default function StoragePage() {
  return (
    <Suspense fallback={null}>
      <StorageContent />
    </Suspense>
  );
}

async function StorageContent() {
  const session = await getSessionMetaFromCookies();
  let profile: Awaited<ReturnType<typeof getCurrentUserProfile>> = null;
  if (session) {
    try {
      profile = await getCurrentUserProfile();
    } catch (error) {
      console.warn('[storage] Failed to load current user profile', error);
    }
  }

  const canManageStorage = isTenantAdmin({
    role: profile?.role ?? null,
    scopes: session?.scopes ?? null,
  });

  if (!canManageStorage) {
    return (
      <section className="space-y-6">
        <SectionHeader
          eyebrow="Workspace"
          title="Storage console"
          description="Manage uploaded files and vector stores for your tenant."
        />

        <GlassPanel className="space-y-2 border border-warning/40 bg-warning/5">
          <p className="text-base font-semibold text-foreground">Admin role required</p>
          <p className="text-sm text-foreground/70">
            Storage access is restricted to tenant admins and owners. Ask an administrator to upgrade your role,
            then refresh this page.
          </p>
        </GlassPanel>
      </section>
    );
  }

  return <StorageAdmin />;
}

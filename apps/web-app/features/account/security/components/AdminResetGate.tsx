'use client';

import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { ADMIN_RESET_DOC_URL } from '../constants';
import { AdminPasswordResetCard } from '../../components/AdminPasswordResetCard';

interface AdminResetGateProps {
  hasSupportScope: boolean;
  hasTenantContext: boolean;
  tenantName: string | null;
}

export function AdminResetGate({ hasSupportScope, hasTenantContext, tenantName }: AdminResetGateProps) {
  if (hasSupportScope && hasTenantContext) {
    return <AdminPasswordResetCard tenantName={tenantName} />;
  }

  return (
    <GlassPanel className="space-y-4">
      <SectionHeader
        title="Admin password reset"
        description="Restricted to support operators with tenant context. Ask an admin if a teammate is locked out."
        actions={<InlineTag tone="warning">{hasSupportScope ? 'Tenant required' : 'Restricted'}</InlineTag>}
      />
      <p className="text-sm text-foreground/70">
        Initiating a reset on behalf of another user requires both the support:read scope and an active tenant
        context so audit trails keep their actor and tenant attribution. Review the auth threat model before widening
        access.
      </p>
      <div className="flex flex-wrap gap-3">
        <Button asChild variant="outline" size="sm">
          <Link href={ADMIN_RESET_DOC_URL} target="_blank" rel="noreferrer">
            Review auth controls
          </Link>
        </Button>
      </div>
    </GlassPanel>
  );
}

'use client';

import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { SERVICE_ACCOUNTS_DOC_URL } from '../constants';
import { formatDateTime } from '../utils/dates';

interface ProfileQuickActionsCardProps {
  sessionExpiresAt: string | null;
}

export function ProfileQuickActionsCard({ sessionExpiresAt }: ProfileQuickActionsCardProps) {
  return (
    <GlassPanel className="space-y-4">
      <SectionHeader
        title="Metadata & quick actions"
        description="Jump into deeper account tools as needed."
      />
      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-foreground/50">Recent activity</p>
          <div className="mt-2 space-y-2 text-sm text-foreground/80">
            <div className="flex justify-between">
              <span>Last login</span>
              <span className="text-right text-foreground/60">See Sessions</span>
            </div>
            <div className="flex justify-between">
              <span>Session expires</span>
              <span className="text-right">{formatDateTime(sessionExpiresAt)}</span>
            </div>
          </div>
          <Button asChild variant="outline" size="sm" className="mt-3 w-full">
            <Link href="/account?tab=sessions">View sessions</Link>
          </Button>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-foreground/50">Service accounts</p>
          <p className="mt-2 text-sm text-foreground/70">
            Issue or revoke automation tokens from the Automation tab.
          </p>
          <div className="mt-3 flex flex-col gap-2">
            <Button asChild variant="secondary" size="sm">
              <Link href="/account?tab=automation">Open automation</Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href={SERVICE_ACCOUNTS_DOC_URL} target="_blank" rel="noreferrer">
                Console guide
              </Link>
            </Button>
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-foreground/50">Billing</p>
          <p className="mt-2 text-sm text-foreground/70">
            Update plan, seats, and payment details from Billing.
          </p>
          <div className="mt-3 flex flex-col gap-2">
            <Button asChild variant="secondary" size="sm">
              <Link href="/billing">Open billing</Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href="/settings/tenant">Tenant settings</Link>
            </Button>
          </div>
        </div>
      </div>
    </GlassPanel>
  );
}

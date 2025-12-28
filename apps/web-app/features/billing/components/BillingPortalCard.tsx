'use client';

import { ExternalLink } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';
import { useToast } from '@/components/ui/use-toast';
import { useCreatePortalSessionMutation } from '@/lib/queries/billingPortal';

import { BILLING_COPY } from '../constants';

interface BillingPortalCardProps {
  tenantId: string | null;
  billingEmail?: string | null;
}

export function BillingPortalCard({ tenantId, billingEmail }: BillingPortalCardProps) {
  const portalSession = useCreatePortalSessionMutation({ tenantId });
  const { error } = useToast();

  const handleOpenPortal = async () => {
    if (!tenantId) {
      return;
    }
    const popup = window.open('', '_blank');
    try {
      const session = await portalSession.mutateAsync({
        billing_email: billingEmail ?? undefined,
      });
      if (!session.url) {
        throw new Error('Stripe portal URL missing.');
      }
      if (popup) {
        popup.opener = null;
        popup.location.href = session.url;
      } else {
        window.location.assign(session.url);
      }
    } catch (err) {
      if (popup) {
        popup.close();
      }
      error({
        title: 'Unable to open portal',
        description: err instanceof Error ? err.message : 'Please try again.',
      });
    }
  };

  return (
    <GlassPanel className="flex h-full flex-col justify-between gap-4">
      <div className="space-y-2">
        <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">
          {BILLING_COPY.planManagement.portal.title}
        </p>
        <p className="text-sm text-foreground/70">
          {BILLING_COPY.planManagement.portal.description}
        </p>
      </div>
      <Button
        onClick={handleOpenPortal}
        disabled={!tenantId || portalSession.isPending}
        variant="outline"
        className="w-full justify-between"
      >
        {portalSession.isPending ? 'Opening…' : BILLING_COPY.planManagement.portal.ctaLabel}
        <ExternalLink className="h-4 w-4" />
      </Button>
    </GlassPanel>
  );
}

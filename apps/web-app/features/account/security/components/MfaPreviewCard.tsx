'use client';

import Link from 'next/link';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { MFA_DOC_URL } from '../constants';

export function MfaPreviewCard() {
  return (
    <GlassPanel className="space-y-6">
      <SectionHeader
        title="Multi-factor authentication"
        description="Passkeys + TOTP enrollment ship alongside the enterprise security milestone."
        actions={<InlineTag tone="warning">Planned</InlineTag>}
      />
      <p className="text-sm text-foreground/70">
        MFA will support passkeys (WebAuthn) and backup TOTP codes so operators can secure both the dashboard
        and console flows. Admins will be able to enforce tenant-wide MFA once rollout completes.
      </p>
      <div className="flex flex-wrap gap-3">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="secondary" disabled>
                Enable MFA
              </Button>
            </TooltipTrigger>
            <TooltipContent side="top">Coming soon—follow the roadmap for updates.</TooltipContent>
          </Tooltip>
        </TooltipProvider>
        <Button asChild variant="outline">
          <Link href={MFA_DOC_URL} target="_blank" rel="noreferrer">
            View MFA roadmap
          </Link>
        </Button>
      </div>
      <Alert className="border border-warning/40 bg-warning/10 text-warning">
        <AlertTitle>Heads up</AlertTitle>
        <AlertDescription>
          Until MFA ships, make sure every admin uses a password manager and rotates credentials quarterly.
        </AlertDescription>
      </Alert>
    </GlassPanel>
  );
}

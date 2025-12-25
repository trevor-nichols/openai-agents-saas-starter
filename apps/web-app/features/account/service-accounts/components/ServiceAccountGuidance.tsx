'use client';

import Link from 'next/link';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

export function ServiceAccountGuidance() {
  return (
    <Alert>
      <AlertTitle>Need to run this in CI?</AlertTitle>
      <AlertDescription className="space-y-2 text-sm text-foreground/70">
        <p>
          Browser mode signs requests with your admin session. Switch to the Vault-signed mode if your organization requires pre-signed headers from Vault Transit. CI pipelines can continue using the Console via
          <code className="ml-1 rounded bg-muted px-2 py-1 text-xs font-mono">starter-console auth tokens issue-service-account</code>.
        </p>
        <p>
          Latest rollout status lives in
          <Link className="ml-1 underline" href="/docs/frontend/features/account-service-accounts.md">
            docs/frontend/features/account-service-accounts.md
          </Link>
          .
        </p>
      </AlertDescription>
    </Alert>
  );
}

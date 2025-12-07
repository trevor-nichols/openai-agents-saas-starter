"use client";

import { Button } from "@/components/ui/button";
import { GlassPanel, SectionHeader } from "@/components/ui/foundation";
import { Skeleton } from "@/components/ui/skeleton";
import { useConsentsQuery } from "@/lib/queries/consents";

export function ConsentsCard() {
  const { data, isLoading, error, refetch } = useConsentsQuery();

  return (
    <GlassPanel className="space-y-4">
      <SectionHeader
        eyebrow="Privacy"
        title="Policy acknowledgements"
        description="Versioned consent records for this account."
        actions={
          <Button size="sm" variant="ghost" onClick={() => refetch()} disabled={isLoading}>
            Refresh
          </Button>
        }
      />

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : error ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          <div className="flex items-center justify-between gap-3">
            <p>{error instanceof Error ? error.message : 'Failed to load consent history.'}</p>
            <Button size="sm" variant="ghost" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        </div>
      ) : data && data.length > 0 ? (
        <div className="divide-y divide-border rounded-md border">
          {data.map((consent) => (
            <div key={`${consent.policy_key}-${consent.version}`} className="flex items-center justify-between px-3 py-2 text-sm">
              <div>
                <p className="font-medium">{consent.policy_key}</p>
                <p className="text-xs text-muted-foreground">Version {consent.version}</p>
              </div>
              <span className="text-xs text-muted-foreground">{new Date(consent.accepted_at).toLocaleString()}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No consent records found.</p>
      )}
    </GlassPanel>
  );
}

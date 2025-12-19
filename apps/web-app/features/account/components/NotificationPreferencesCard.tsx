"use client";

import { useMemo } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { GlassPanel, SectionHeader } from "@/components/ui/foundation";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { useNotificationPreferencesQuery, useUpsertNotificationPreferenceMutation } from "@/lib/queries/notificationPreferences";
import { useToast } from "@/components/ui/use-toast";

export function NotificationPreferencesCard() {
  const { success, error: errorToast } = useToast();
  const { data, isLoading, error, refetch } = useNotificationPreferencesQuery();
  const mutation = useUpsertNotificationPreferenceMutation();

  const grouped = useMemo(() => {
    const items = data ?? [];
    return items.reduce<Record<string, typeof items>>((acc, pref) => {
      const key = pref.channel;
      acc[key] = acc[key] ? [...acc[key], pref] : [pref];
      return acc;
    }, {});
  }, [data]);

  const handleToggle = async (_id: string, channel: string, category: string, enabled: boolean) => {
    try {
      await mutation.mutateAsync({ channel, category, enabled });
      await refetch();
      success({ title: "Preference updated" });
    } catch (error) {
      errorToast({
        title: "Unable to update",
        description: error instanceof Error ? error.message : "Try again",
      });
    }
  };

  return (
    <GlassPanel className="space-y-4">
      <SectionHeader
        eyebrow="Notifications"
        title="Channel preferences"
        description="Choose which updates you receive across channels."
        actions={<Badge variant="outline">Tenant scoped</Badge>}
      />

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : error ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          <div className="flex items-center justify-between gap-3">
            <p>{error instanceof Error ? error.message : 'Failed to load notification preferences.'}</p>
            <Button size="sm" variant="ghost" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        </div>
      ) : data && data.length > 0 ? (
        <div className="space-y-4">
          {Object.entries(grouped).map(([channel, prefs]) => (
            <div key={channel} className="space-y-2 rounded-md border p-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium capitalize">{channel}</p>
                <Badge variant="secondary">{prefs.length} categories</Badge>
              </div>
              <div className="space-y-2">
                {prefs.map((pref) => (
                  <div key={pref.id} className="flex items-center justify-between rounded bg-muted/50 px-3 py-2 text-sm">
                    <span className="font-medium">{pref.category}</span>
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={pref.enabled}
                        onCheckedChange={(checked) => handleToggle(pref.id, pref.channel, pref.category, checked)}
                        disabled={mutation.isPending}
                        aria-label={`Toggle ${pref.channel} ${pref.category}`}
                      />
                      <span className="text-xs text-muted-foreground">{pref.enabled ? "On" : "Off"}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
          No preferences found. They’ll appear here once configured on the backend.
        </div>
      )}

      <div className="flex items-center justify-between rounded-md border border-dashed px-3 py-2 text-xs text-muted-foreground">
        <span>Preferences respect tenant scoping; admin-level overrides are coming later.</span>
        <Button size="sm" variant="ghost" onClick={() => refetch()} disabled={isLoading || mutation.isPending}>
          Refresh
        </Button>
      </div>
    </GlassPanel>
  );
}

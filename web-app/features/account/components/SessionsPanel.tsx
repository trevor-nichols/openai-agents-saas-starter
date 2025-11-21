'use client';

import { useCallback, useMemo, useState } from 'react';
import type { ColumnDef } from '@tanstack/react-table';

import { DataTable } from '@/components/ui/data-table';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import { EmptyState, ErrorState } from '@/components/ui/states';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useToast } from '@/components/ui/use-toast';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAccountProfileQuery } from '@/lib/queries/account';
import { useLogoutAllSessionsMutation, useRevokeSessionMutation, useUserSessionsQuery, type SessionRow } from '@/lib/queries/accountSessions';

const DEFAULT_LIMIT = 50;

type TenantFilterOption = 'all' | 'current' | 'custom';

export function SessionsPanel() {
  const { profile } = useAccountProfileQuery();
  const [tenantFilterMode, setTenantFilterMode] = useState<TenantFilterOption>('all');
  const [customTenantId, setCustomTenantId] = useState('');

  const resolvedTenantId = useMemo(() => {
    if (tenantFilterMode === 'current') {
      return profile?.tenant?.id ?? null;
    }
    if (tenantFilterMode === 'custom') {
      const value = customTenantId.trim();
      return value.length > 0 ? value : null;
    }
    return null;
  }, [customTenantId, tenantFilterMode, profile?.tenant?.id]);

  const sessionsQuery = useUserSessionsQuery({ limit: DEFAULT_LIMIT, tenantId: resolvedTenantId });
  const revokeSession = useRevokeSessionMutation();
  const logoutAll = useLogoutAllSessionsMutation();
  const toast = useToast();
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleRevoke = useCallback(async (sessionId: string) => {
    try {
      await revokeSession.mutateAsync(sessionId);
      toast.success({ title: 'Session revoked', description: 'The device was signed out.' });
    } catch (error) {
      toast.error({
        title: 'Unable to revoke session',
        description: error instanceof Error ? error.message : 'Try again shortly.',
      });
    }
  }, [revokeSession, toast]);

  const handleLogoutAll = async () => {
    setConfirmOpen(false);
    try {
      const result = await logoutAll.mutateAsync();
      const count = result.data?.revoked ?? undefined;
      toast.success({
        title: 'Signed out everywhere',
        description: count ? `Revoked ${count} session${count === 1 ? '' : 's'}.` : 'All sessions have been revoked.',
      });
      setTimeout(() => {
        window.location.href = '/login';
      }, 1200);
    } catch (error) {
      toast.error({
        title: 'Unable to sign out everywhere',
        description: error instanceof Error ? error.message : 'Try again shortly.',
      });
    }
  };

  const columns = useMemo<ColumnDef<SessionRow>[]>(
    () => [
      {
        header: 'Device',
        cell: ({ row }) => {
          const device = row.original.client?.device ?? 'Unknown device';
          const platform = row.original.client?.platform ?? row.original.client?.browser ?? '—';
          return (
            <div className="flex flex-col">
              <span className="font-medium text-foreground">{device}</span>
              <span className="text-xs text-foreground/60">{platform}</span>
            </div>
          );
        },
      },
      {
        header: 'IP / Location',
        cell: ({ row }) => {
          const ip = row.original.ip_address_masked ?? '—';
          const location = formatLocation(row.original.location);
          return (
            <div className="flex flex-col">
              <span>{ip}</span>
              <span className="text-xs text-foreground/60">{location}</span>
            </div>
          );
        },
      },
      {
        header: 'Last active',
        cell: ({ row }) => <span>{formatDateTime(row.original.last_seen_at)}</span>,
      },
      {
        header: 'Created',
        cell: ({ row }) => <span>{formatDateTime(row.original.created_at)}</span>,
      },
      {
        header: 'Status',
        cell: ({ row }) => (
          <InlineTag tone={row.original.current ? 'positive' : row.original.revoked_at ? 'warning' : 'default'}>
            {row.original.current ? 'Current' : row.original.revoked_at ? 'Revoked' : 'Active'}
          </InlineTag>
        ),
      },
      {
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <Button
            size="sm"
            variant="outline"
            disabled={row.original.current || revokeSession.isPending}
            onClick={() => handleRevoke(row.original.id)}
          >
            Revoke
          </Button>
        ),
      },
    ],
    [handleRevoke, revokeSession.isPending],
  );

  const isLoading = sessionsQuery.isLoading;
  const loadError = sessionsQuery.error instanceof Error ? sessionsQuery.error.message : undefined;
  const data = sessionsQuery.data?.sessions ?? [];
  const total = sessionsQuery.data?.total ?? data.length;

  return (
    <section className="space-y-6">
      <SectionHeader
        eyebrow="Account"
        title="Active sessions"
        description="Review recent devices and sign out sessions you no longer trust."
      />

      <GlassPanel className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-foreground/70">Active sessions</p>
            <p className="text-2xl font-semibold text-foreground">{total}</p>
          </div>
          {profile?.verification.emailVerified === false ? (
            <InlineTag tone="warning">Email unverified</InlineTag>
          ) : null}
        </div>
        <div className="rounded-lg border border-white/10 bg-white/5 p-3 text-xs text-foreground/60">
          Revoke sessions you do not recognize. Selecting Sign out everywhere will also log you out of this browser.
        </div>
      </GlassPanel>

      <GlassPanel className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <Select value={tenantFilterMode} onValueChange={(value) => setTenantFilterMode(value as TenantFilterOption)}>
              <SelectTrigger className="w-[220px]">
                <SelectValue placeholder="Tenant filter" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All tenants</SelectItem>
                <SelectItem value="current" disabled={!profile?.tenant?.id}>
                  Current tenant
                </SelectItem>
                <SelectItem value="custom">Specific tenant ID</SelectItem>
              </SelectContent>
            </Select>
            {tenantFilterMode === 'custom' ? (
              <Input
                className="w-full max-w-xs"
                placeholder="Tenant UUID"
                value={customTenantId}
                onChange={(event) => setCustomTenantId(event.target.value)}
              />
            ) : null}
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setConfirmOpen(true)}
                  disabled={logoutAll.isPending || isLoading || data.length === 0}
                >
                  Sign out everywhere
                </Button>
              </TooltipTrigger>
              <TooltipContent side="left">Logs out every session, including this one.</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        <p className="text-xs text-foreground/60">
          Viewing {resolvedTenantId ? `sessions scoped to tenant ${resolvedTenantId}` : 'sessions across all tenants'}.
        </p>

        {loadError && !isLoading ? (
          <ErrorState title="Unable to load sessions" message={loadError} onRetry={() => sessionsQuery.refetch()} />
        ) : (
          <DataTable<SessionRow>
            columns={columns}
            data={data}
            isLoading={isLoading}
            emptyState={<EmptyState title="No sessions" description="We did not find any active sessions." />}
          />
        )}
      </GlassPanel>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Sign out everywhere?</AlertDialogTitle>
            <AlertDialogDescription>
              This will revoke every active session, including this browser. You will need to sign in again afterwards.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={logoutAll.isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction disabled={logoutAll.isPending} onClick={handleLogoutAll} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Confirm
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  );
}

function formatLocation(location?: SessionRow['location'] | null): string {
  if (!location) {
    return 'Unknown location';
  }
  const parts = [location.city, location.region, location.country].filter(Boolean);
  return parts.length ? parts.join(', ') : 'Unknown location';
}

function formatDateTime(value: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }
  return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

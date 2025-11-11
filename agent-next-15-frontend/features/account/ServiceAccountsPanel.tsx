'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState, type ComponentProps } from 'react';
import type { ColumnDef } from '@tanstack/react-table';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/ui/data-table';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import { EmptyState, ErrorState } from '@/components/ui/states';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import {
  useRevokeServiceAccountTokenMutation,
  useServiceAccountTokensQuery,
} from '@/lib/queries/accountServiceAccounts';
import type { ServiceAccountStatusFilter, ServiceAccountTokenRow } from '@/types/serviceAccounts';

const DEFAULT_LIMIT = 50;
const STATUS_OPTIONS: { label: string; value: ServiceAccountStatusFilter }[] = [
  { label: 'Active', value: 'active' },
  { label: 'Revoked', value: 'revoked' },
  { label: 'All', value: 'all' },
];

export function ServiceAccountsPanel() {
  const toast = useToast();
  const [accountSearch, setAccountSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<ServiceAccountStatusFilter>('active');
  const debouncedAccount = useDebouncedValue(accountSearch, 350);

  const queryFilters = useMemo(
    () => ({
      account: debouncedAccount || undefined,
      status: statusFilter,
      limit: DEFAULT_LIMIT,
      offset: 0,
    }),
    [debouncedAccount, statusFilter],
  );

  const tokensQuery = useServiceAccountTokensQuery(queryFilters);
  const revokeMutation = useRevokeServiceAccountTokenMutation();

  const [dialogState, setDialogState] = useState<{
    token: ServiceAccountTokenRow | null;
    reason: string;
  }>({ token: null, reason: '' });

  const openRevokeDialog = useCallback((token: ServiceAccountTokenRow) => {
    setDialogState({ token, reason: '' });
  }, []);

  const closeDialog = useCallback(() => {
    setDialogState({ token: null, reason: '' });
  }, []);

  const handleConfirmRevoke = useCallback(async () => {
    if (!dialogState.token) return;
    try {
      await revokeMutation.mutateAsync({
        tokenId: dialogState.token.id,
        reason: dialogState.reason,
      });
      toast.success({
        title: 'Token revoked',
        description: `${dialogState.token.account} tokens can no longer refresh.`,
      });
      closeDialog();
    } catch (error) {
      toast.error({
        title: 'Unable to revoke token',
        description: error instanceof Error ? error.message : 'Try again shortly.',
      });
    }
  }, [closeDialog, dialogState.reason, dialogState.token, revokeMutation, toast]);

  const columns = useMemo<ColumnDef<ServiceAccountTokenRow>[]>(
    () => [
      {
        header: 'Account',
        cell: ({ row }) => (
          <div className="flex flex-col">
            <span className="font-medium text-foreground">{row.original.account}</span>
            <span className="text-xs text-foreground/60">
              {row.original.fingerprint || row.original.id}
            </span>
          </div>
        ),
      },
      {
        header: 'Scopes',
        cell: ({ row }) => (
          <div className="flex flex-wrap gap-1">
            {row.original.scopes.map((scope) => (
              <InlineTag key={scope} tone="default">
                {scope}
              </InlineTag>
            ))}
          </div>
        ),
      },
      {
        header: 'Lifecycle',
        cell: ({ row }) => (
          <div className="flex flex-col text-sm">
            <span>Issued {formatDate(row.original.issuedAt)}</span>
            <span className="text-xs text-foreground/60">Expires {formatDate(row.original.expiresAt)}</span>
          </div>
        ),
      },
      {
        header: 'Status',
        cell: ({ row }) => {
          const status = resolveStatus(row.original);
          return <InlineTag tone={status.tone}>{status.label}</InlineTag>;
        },
      },
      {
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <Button
            size="sm"
            variant="outline"
            disabled={row.original.revokedAt !== null || revokeMutation.isPending}
            onClick={() => openRevokeDialog(row.original)}
          >
            Revoke
          </Button>
        ),
      },
    ],
    [openRevokeDialog, revokeMutation.isPending],
  );

  const tokens = tokensQuery.data?.tokens ?? [];
  const total = tokensQuery.data?.total ?? tokens.length;
  const isLoading = tokensQuery.isLoading;
  const loadError = tokensQuery.error instanceof Error ? tokensQuery.error.message : undefined;

  return (
    <section className="space-y-6">
      <SectionHeader
        eyebrow="Automation"
        title="Service-account tokens"
        description="Inspect automation credentials, audit scopes, and revoke stale tokens."
      />

      <GlassPanel className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-foreground/70">Total tokens</p>
            <p className="text-2xl font-semibold text-foreground">{total}</p>
          </div>
          <Button variant="outline" size="sm" onClick={() => tokensQuery.refetch()} disabled={tokensQuery.isFetching}>
            Refresh
          </Button>
        </div>
        <p className="text-sm text-foreground/60">
          Issuance still runs through the Starter CLI so Vault-signed credentials never hit the browser. Use this table to
          audit and revoke tokens instantly without leaving the dashboard.
        </p>
      </GlassPanel>

      <GlassPanel className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <Input
            className="w-full max-w-xs"
            placeholder="Search account"
            value={accountSearch}
            onChange={(event) => setAccountSearch(event.target.value)}
          />
          <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as ServiceAccountStatusFilter)}>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              {STATUS_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {loadError && !isLoading ? (
          <ErrorState
            title="Unable to load tokens"
            message={loadError}
            onRetry={() => tokensQuery.refetch()}
          />
        ) : (
          <DataTable<ServiceAccountTokenRow>
            columns={columns}
            data={tokens}
            isLoading={isLoading}
            emptyState={<EmptyState title="No service-account tokens" description="Issue a token via the Starter CLI to see it here." />}
          />
        )}
      </GlassPanel>

      <Alert>
        <AlertTitle>Issuing tokens</AlertTitle>
        <AlertDescription className="space-y-2 text-sm text-foreground/70">
          <p>
            Use the Starter CLI to mint tokens with Vault-signed credentials. Run
            <code className="ml-1 rounded bg-muted px-2 py-1 text-xs font-mono">starter_cli auth tokens issue-service-account</code>
            and the resulting refresh token will appear in this table within a few seconds.
          </p>
          <p>
            Review the latest rollout notes in
            <Link className="ml-1 underline" href="/docs/frontend/features/account-service-accounts.md">
              docs/frontend/features/account-service-accounts.md
            </Link>
            .
          </p>
        </AlertDescription>
      </Alert>

      <AlertDialog open={Boolean(dialogState.token)} onOpenChange={(open) => { if (!open) closeDialog(); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Revoke {dialogState.token?.account}</AlertDialogTitle>
            <AlertDialogDescription>
              This immediately invalidates the refresh token. Automation pipelines using it will need a new credential.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="space-y-2 py-2">
            <Textarea
              placeholder="Optional reason (shown in audit logs)"
              value={dialogState.reason}
              onChange={(event) => setDialogState((current) => ({ ...current, reason: event.target.value }))}
              disabled={revokeMutation.isPending}
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={revokeMutation.isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={revokeMutation.isPending}
              onClick={handleConfirmRevoke}
            >
              Revoke token
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  );
}

type InlineTagTone = ComponentProps<typeof InlineTag>['tone'];

function resolveStatus(token: ServiceAccountTokenRow): { label: string; tone: InlineTagTone } {
  if (token.revokedAt) {
    return { label: 'Revoked', tone: 'warning' };
  }
  if (isPast(token.expiresAt)) {
    return { label: 'Expired', tone: 'default' };
  }
  return { label: 'Active', tone: 'positive' };
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }
  return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

function isPast(value: string): boolean {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return false;
  }
  return date.getTime() < Date.now();
}

function useDebouncedValue<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}

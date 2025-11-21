'use client';

import { useCallback, useMemo, useState } from 'react';
import type { ColumnDef } from '@tanstack/react-table';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { DataTable } from '@/components/ui/data-table';
import { useToast } from '@/components/ui/use-toast';
import {
  useIssueSignupInviteMutation,
  useRevokeSignupInviteMutation,
  useSignupInvitesQuery,
} from '@/lib/queries/signup';
import type { SignupInviteStatusFilter, SignupInviteSummary } from '@/types/signup';

import { formatDateTime, formatStatus } from '../utils';
import { IssueInviteDialog } from './IssueInviteDialog';

const STATUS_OPTIONS: Array<{ value: SignupInviteStatusFilter | 'all'; label: string }> = [
  { value: 'all', label: 'All statuses' },
  { value: 'active', label: 'Active' },
  { value: 'revoked', label: 'Revoked' },
  { value: 'expired', label: 'Expired' },
  { value: 'exhausted', label: 'Exhausted' },
];

export function InvitesPanel() {
  const [statusFilter, setStatusFilter] = useState<SignupInviteStatusFilter | 'all'>('active');
  const [searchInput, setSearchInput] = useState('');
  const [emailFilter, setEmailFilter] = useState('');
  const [isDialogOpen, setDialogOpen] = useState(false);
  const toast = useToast();

  const filters = useMemo(
    () => ({
      status: statusFilter === 'all' ? undefined : statusFilter,
      email: emailFilter || undefined,
    }),
    [statusFilter, emailFilter],
  );

  const { data, isLoading, error, refetch } = useSignupInvitesQuery(filters);
  const revokeMutation = useRevokeSignupInviteMutation();
  const issueMutation = useIssueSignupInviteMutation();

  const handleApplySearch = () => {
    setEmailFilter(searchInput.trim());
  };

  const handleRevoke = useCallback(
    async (invite: SignupInviteSummary) => {
      try {
        await revokeMutation.mutateAsync({ inviteId: invite.id });
        toast.success({
          title: 'Invite revoked',
          description: `The invite ${invite.tokenHint} can no longer be used.`,
        });
        refetch();
      } catch (err) {
        const description = err instanceof Error ? err.message : 'Unable to revoke invite.';
        toast.error({ title: 'Revoke failed', description });
      }
    },
    [revokeMutation, toast, refetch],
  );

  const columns: ColumnDef<SignupInviteSummary>[] = useMemo(
    () => [
      {
        accessorKey: 'tokenHint',
        header: 'Invite token',
        cell: ({ row }) => <span className="font-mono text-sm">{row.original.tokenHint ?? 'Hidden'}</span>,
      },
      {
        accessorKey: 'invitedEmail',
        header: 'Email restriction',
        cell: ({ row }) => row.original.invitedEmail ?? 'Any email',
      },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: ({ row }) => <Badge variant="outline">{formatStatus(row.original.status)}</Badge>,
      },
      {
        accessorKey: 'redeemedCount',
        header: 'Redemptions',
        cell: ({ row }) => `${row.original.redeemedCount}/${row.original.maxRedemptions}`,
      },
      {
        accessorKey: 'expiresAt',
        header: 'Expires',
        cell: ({ row }) => formatDateTime(row.original.expiresAt),
      },
      {
        accessorKey: 'createdAt',
        header: 'Created',
        cell: ({ row }) => formatDateTime(row.original.createdAt),
      },
      {
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <div className="flex gap-2">
            {row.original.status === 'active' ? (
              <Button variant="outline" size="sm" onClick={() => handleRevoke(row.original)}>
                Revoke
              </Button>
            ) : null}
          </div>
        ),
      },
    ],
    [handleRevoke],
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as SignupInviteStatusFilter | 'all')}>
          <SelectTrigger className="w-40">
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

        <div className="flex flex-1 gap-2 min-w-[240px]">
          <Input
            placeholder="Filter by email"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                handleApplySearch();
              }
            }}
          />
          <Button variant="outline" onClick={handleApplySearch}>
            Search
          </Button>
        </div>

        <Button onClick={() => setDialogOpen(true)}>Issue invite</Button>
      </div>

      <DataTable
        columns={columns}
        data={data?.invites ?? []}
        isLoading={isLoading}
        isError={Boolean(error)}
        error={error?.message}
        skeletonLines={6}
      />

      <IssueInviteDialog
        open={isDialogOpen}
        onOpenChange={setDialogOpen}
        isSubmitting={issueMutation.isPending}
        onSubmit={async (payload) => {
          try {
            await issueMutation.mutateAsync(payload);
            toast.success({ title: 'Invite issued', description: 'Share the token with the requester.' });
            setDialogOpen(false);
            refetch();
          } catch (err) {
            const description = err instanceof Error ? err.message : 'Unable to issue invite.';
            toast.error({ title: 'Issue invite failed', description });
          }
        }}
      />
    </div>
  );
}

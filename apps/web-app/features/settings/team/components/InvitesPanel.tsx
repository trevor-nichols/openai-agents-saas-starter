'use client';

import { useCallback, useMemo, useState } from 'react';
import type { ColumnDef } from '@tanstack/react-table';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/ui/data-table';
import { EmptyState } from '@/components/ui/states';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { useAccountProfileQuery } from '@/lib/queries/account';
import {
  useIssueTeamInviteMutation,
  useRevokeTeamInviteMutation,
  useTeamInvitesQuery,
} from '@/lib/queries/team';
import type { TeamInviteIssueResult, TeamInviteStatusFilter, TeamInviteSummary, TeamRole } from '@/types/team';

import { TEAM_ROLE_HELPERS, TEAM_ROLE_LABELS, TEAM_SETTINGS_COPY } from '../constants';
import { formatDateTime, formatStatus, getAssignableRoles, resolveRoleLabel } from '../utils';
import { InviteMemberDialog } from './InviteMemberDialog';
import { InviteTokenDialog } from './InviteTokenDialog';

const STATUS_OPTIONS: Array<{ value: TeamInviteStatusFilter | 'all'; label: string }> = [
  { value: 'all', label: 'All statuses' },
  { value: 'active', label: 'Active' },
  { value: 'accepted', label: 'Accepted' },
  { value: 'revoked', label: 'Revoked' },
  { value: 'expired', label: 'Expired' },
];

export function InvitesPanel() {
  const [statusFilter, setStatusFilter] = useState<TeamInviteStatusFilter | 'all'>('active');
  const [searchInput, setSearchInput] = useState('');
  const [emailFilter, setEmailFilter] = useState('');
  const [isDialogOpen, setDialogOpen] = useState(false);
  const [issuedInvite, setIssuedInvite] = useState<TeamInviteIssueResult | null>(null);

  const toast = useToast();
  const { profile } = useAccountProfileQuery();
  const actorRole = profile?.user.role ?? null;
  const assignableRoles = useMemo(() => getAssignableRoles(actorRole), [actorRole]);
  const roleOptions = useMemo(
    () =>
      (assignableRoles.length > 0 ? assignableRoles : (['member'] as TeamRole[])).map((role) => ({
        value: role,
        label: TEAM_ROLE_LABELS[role],
        helper: TEAM_ROLE_HELPERS[role],
      })),
    [assignableRoles],
  );

  const filters = useMemo(
    () => ({
      status: statusFilter === 'all' ? undefined : statusFilter,
      email: emailFilter || undefined,
    }),
    [statusFilter, emailFilter],
  );

  const { data, isLoading, error, refetch } = useTeamInvitesQuery(filters);
  const revokeMutation = useRevokeTeamInviteMutation();
  const issueMutation = useIssueTeamInviteMutation();

  const handleApplySearch = () => {
    setEmailFilter(searchInput.trim());
  };

  const handleRevoke = useCallback(
    async (invite: TeamInviteSummary) => {
      try {
        await revokeMutation.mutateAsync({ inviteId: invite.id });
        toast.success({
          title: 'Invite revoked',
          description: `${invite.invitedEmail} can no longer use this invite.`,
        });
        refetch();
      } catch (err) {
        const description = err instanceof Error ? err.message : 'Unable to revoke invite.';
        toast.error({ title: 'Revoke failed', description });
      }
    },
    [revokeMutation, toast, refetch],
  );

  const columns = useMemo<ColumnDef<TeamInviteSummary>[]>(
    () => [
      {
        accessorKey: 'invitedEmail',
        header: 'Invitee',
        cell: ({ row }) => row.original.invitedEmail,
      },
      {
        accessorKey: 'role',
        header: 'Role',
        cell: ({ row }) => resolveRoleLabel(row.original.role),
      },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: ({ row }) => <Badge variant="outline">{formatStatus(row.original.status)}</Badge>,
      },
      {
        accessorKey: 'tokenHint',
        header: 'Token hint',
        cell: ({ row }) => <span className="font-mono text-xs">{row.original.tokenHint}</span>,
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
        <Select
          value={statusFilter}
          onValueChange={(value) => setStatusFilter(value as TeamInviteStatusFilter | 'all')}
        >
          <SelectTrigger className="w-44">
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

        <Button onClick={() => setDialogOpen(true)} disabled={assignableRoles.length === 0}>
          Issue invite
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={data?.invites ?? []}
        isLoading={isLoading}
        isError={Boolean(error)}
        error={error?.message}
        emptyState={
          <EmptyState
            title={TEAM_SETTINGS_COPY.emptyInvites.title}
            description={TEAM_SETTINGS_COPY.emptyInvites.description}
          />
        }
        skeletonLines={6}
      />

      <InviteMemberDialog
        open={isDialogOpen}
        onOpenChange={setDialogOpen}
        isSubmitting={issueMutation.isPending}
        roleOptions={roleOptions}
        onSubmit={async (payload) => {
          const result = await issueMutation.mutateAsync(payload);
          toast.success({
            title: 'Invite issued',
            description: 'Share the invite token with your teammate.',
          });
          setDialogOpen(false);
          setIssuedInvite(result);
          refetch();
          return result;
        }}
      />

      <InviteTokenDialog
        open={Boolean(issuedInvite)}
        onOpenChange={(open) => {
          if (!open) {
            setIssuedInvite(null);
          }
        }}
        invite={issuedInvite}
      />
    </div>
  );
}

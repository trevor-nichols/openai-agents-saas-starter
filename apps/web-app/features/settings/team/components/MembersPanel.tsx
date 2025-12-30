'use client';

import { useCallback, useMemo, useState } from 'react';
import type { ColumnDef } from '@tanstack/react-table';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/ui/data-table';
import { EmptyState } from '@/components/ui/states';
import { Input } from '@/components/ui/input';
import { useToast } from '@/components/ui/use-toast';
import { useAccountProfileQuery } from '@/lib/queries/account';
import {
  useAddTeamMemberMutation,
  useRemoveTeamMemberMutation,
  useTeamMembersQuery,
  useUpdateTeamMemberRoleMutation,
} from '@/lib/queries/team';
import type { TeamMemberSummary, TeamRole } from '@/types/team';

import { TEAM_ROLE_HELPERS, TEAM_ROLE_LABELS, TEAM_SETTINGS_COPY } from '../constants';
import {
  canEditMemberRole,
  canRemoveMember,
  formatDateTime,
  formatStatus,
  getAssignableRoles,
  resolveRoleLabel,
} from '../utils';
import { AddMemberDialog } from './AddMemberDialog';
import { RemoveMemberDialog } from './RemoveMemberDialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export function MembersPanel() {
  const [searchInput, setSearchInput] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [isAddDialogOpen, setAddDialogOpen] = useState(false);
  const [memberToRemove, setMemberToRemove] = useState<TeamMemberSummary | null>(null);

  const toast = useToast();
  const { data, isLoading, error, refetch } = useTeamMembersQuery();
  const addMutation = useAddTeamMemberMutation();
  const updateRoleMutation = useUpdateTeamMemberRoleMutation();
  const removeMutation = useRemoveTeamMemberMutation();

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

  const members = useMemo(() => data?.members ?? [], [data?.members]);
  const ownerCount = data?.ownerCount;

  const filteredMembers = useMemo(() => {
    if (!searchTerm) return members;
    const normalized = searchTerm.toLowerCase();
    return members.filter((member) => {
      const name = member.displayName?.toLowerCase() ?? '';
      const email = member.email.toLowerCase();
      return name.includes(normalized) || email.includes(normalized);
    });
  }, [members, searchTerm]);

  const handleRoleChange = useCallback(
    async (member: TeamMemberSummary, nextRole: TeamRole) => {
      if (member.role === nextRole) return;
      try {
        await updateRoleMutation.mutateAsync({
          userId: member.userId,
          payload: { role: nextRole },
        });
        toast.success({
          title: 'Role updated',
          description: `${member.email} is now ${resolveRoleLabel(nextRole)}.`,
        });
      } catch (err) {
        const description = err instanceof Error ? err.message : 'Unable to update role.';
        toast.error({ title: 'Role update failed', description });
      }
    },
    [toast, updateRoleMutation],
  );

  const handleRemove = useCallback(
    async (member: TeamMemberSummary) => {
      try {
        await removeMutation.mutateAsync({ userId: member.userId });
        toast.success({
          title: 'Member removed',
          description: `${member.email} no longer has access.`,
        });
        setMemberToRemove(null);
      } catch (err) {
        const description = err instanceof Error ? err.message : 'Unable to remove member.';
        toast.error({ title: 'Remove failed', description });
      }
    },
    [removeMutation, toast],
  );

  const columns = useMemo<ColumnDef<TeamMemberSummary>[]>(
    () => [
      {
        header: 'Member',
        cell: ({ row }) => (
          <div className="flex flex-col">
            <span className="font-medium text-foreground">
              {row.original.displayName ?? row.original.email}
            </span>
            <span className="text-xs text-foreground/60">{row.original.email}</span>
          </div>
        ),
      },
      {
        header: 'Role',
        cell: ({ row }) => {
          const canEdit = canEditMemberRole(actorRole, row.original.role, ownerCount);
          if (!canEdit) {
            return <Badge variant="outline">{resolveRoleLabel(row.original.role)}</Badge>;
          }
          return (
            <Select
              value={row.original.role}
              onValueChange={(value) => handleRoleChange(row.original, value as TeamRole)}
            >
              <SelectTrigger className="h-8 w-40">
                <SelectValue placeholder="Select role" />
              </SelectTrigger>
              <SelectContent>
                {assignableRoles.map((role) => (
                  <SelectItem key={role} value={role}>
                    {TEAM_ROLE_LABELS[role]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          );
        },
      },
      {
        header: 'Status',
        cell: ({ row }) => <Badge variant="outline">{formatStatus(row.original.status)}</Badge>,
      },
      {
        header: 'Joined',
        cell: ({ row }) => formatDateTime(row.original.joinedAt),
      },
      {
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => {
          const allowRemove = canRemoveMember(actorRole, row.original.role, ownerCount);
          return (
            <Button
              size="sm"
              variant="outline"
              disabled={!allowRemove || removeMutation.isPending}
              onClick={() => setMemberToRemove(row.original)}
            >
              Remove
            </Button>
          );
        },
      },
    ],
    [
      actorRole,
      assignableRoles,
      handleRoleChange,
      ownerCount,
      removeMutation.isPending,
    ],
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex flex-1 gap-2 min-w-[240px]">
          <Input
            placeholder="Search by name or email"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                setSearchTerm(searchInput.trim());
              }
            }}
          />
          <Button variant="outline" onClick={() => setSearchTerm(searchInput.trim())}>
            Search
          </Button>
        </div>

        <Button onClick={() => setAddDialogOpen(true)} disabled={assignableRoles.length === 0}>
          Add member
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={filteredMembers}
        isLoading={isLoading}
        isError={Boolean(error)}
        error={error?.message}
        emptyState={
          <EmptyState
            title={TEAM_SETTINGS_COPY.emptyMembers.title}
            description={TEAM_SETTINGS_COPY.emptyMembers.description}
          />
        }
      />

      <AddMemberDialog
        open={isAddDialogOpen}
        onOpenChange={setAddDialogOpen}
        isSubmitting={addMutation.isPending}
        roleOptions={roleOptions}
        onSubmit={async (payload) => {
          try {
            await addMutation.mutateAsync(payload);
            toast.success({
              title: 'Member added',
              description: `${payload.email} now has access.`,
            });
            setAddDialogOpen(false);
            refetch();
          } catch (err) {
            const description = err instanceof Error ? err.message : 'Unable to add member.';
            toast.error({ title: 'Add member failed', description });
          }
        }}
      />

      <RemoveMemberDialog
        open={Boolean(memberToRemove)}
        onOpenChange={(open) => {
          if (!open) {
            setMemberToRemove(null);
          }
        }}
        member={memberToRemove}
        isRemoving={removeMutation.isPending}
        onConfirm={handleRemove}
      />
    </div>
  );
}

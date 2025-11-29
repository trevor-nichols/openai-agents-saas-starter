'use client';

import { useMemo, useState } from 'react';
import type { ColumnDef } from '@tanstack/react-table';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { DataTable } from '@/components/ui/data-table';
import { useToast } from '@/components/ui/use-toast';
import {
  useApproveSignupRequestMutation,
  useRejectSignupRequestMutation,
  useSignupRequestsQuery,
} from '@/lib/queries/signup';
import type { SignupRequestStatusFilter, SignupRequestSummary } from '@/types/signup';

import { formatDateTime, formatStatus } from '../utils';
import { ApproveRequestDialog } from './ApproveRequestDialog';
import { RejectRequestDialog } from './RejectRequestDialog';

const STATUS_OPTIONS: Array<{ value: SignupRequestStatusFilter | 'all'; label: string }> = [
  { value: 'all', label: 'All statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
];

export function RequestsPanel() {
  const [statusFilter, setStatusFilter] = useState<SignupRequestStatusFilter | 'all'>('pending');
  const [requestToApprove, setRequestToApprove] = useState<SignupRequestSummary | null>(null);
  const [requestToReject, setRequestToReject] = useState<SignupRequestSummary | null>(null);
  const toast = useToast();

  const filters = useMemo(
    () => ({
      status: statusFilter === 'all' ? undefined : statusFilter,
    }),
    [statusFilter],
  );

  const { data, isLoading, error, refetch } = useSignupRequestsQuery(filters);
  const approveMutation = useApproveSignupRequestMutation();
  const rejectMutation = useRejectSignupRequestMutation();

  const columns: ColumnDef<SignupRequestSummary>[] = useMemo(
    () => [
      {
        accessorKey: 'email',
        header: 'Email',
        cell: ({ row }) => (
          <div className="flex flex-col">
            <span>{row.original.email}</span>
            {row.original.organization ? (
              <span className="text-xs text-foreground/60">{row.original.organization}</span>
            ) : null}
          </div>
        ),
      },
      {
        accessorKey: 'fullName',
        header: 'Name',
        cell: ({ row }) => row.original.fullName ?? '—',
      },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: ({ row }) => <Badge variant="outline">{formatStatus(row.original.status)}</Badge>,
      },
      {
        accessorKey: 'createdAt',
        header: 'Submitted',
        cell: ({ row }) => formatDateTime(row.original.createdAt),
      },
      {
        accessorKey: 'decisionReason',
        header: 'Decision note',
        cell: ({ row }) => row.original.decisionReason ?? '—',
      },
      {
        accessorKey: 'inviteTokenHint',
        header: 'Invite hint',
        cell: ({ row }) => row.original.inviteTokenHint ?? '—',
      },
      {
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <div className="flex gap-2">
            {row.original.status === 'pending' ? (
              <>
                <Button size="sm" onClick={() => setRequestToApprove(row.original)}>
                  Approve
                </Button>
                <Button size="sm" variant="outline" onClick={() => setRequestToReject(row.original)}>
                  Reject
                </Button>
              </>
            ) : (
              <span className="text-xs text-foreground/50">Resolved</span>
            )}
          </div>
        ),
      },
    ],
    [],
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as SignupRequestStatusFilter | 'all')}>
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
      </div>

      <DataTable
        columns={columns}
        data={data?.requests ?? []}
        isLoading={isLoading}
        isError={Boolean(error)}
        error={error?.message}
        skeletonLines={6}
      />

      <ApproveRequestDialog
        open={Boolean(requestToApprove)}
        onOpenChange={(open) => {
          if (!open) setRequestToApprove(null);
        }}
        request={requestToApprove}
        isSubmitting={approveMutation.isPending}
        onSubmit={async (payload) => {
          if (!requestToApprove) return;
          try {
            await approveMutation.mutateAsync({ requestId: requestToApprove.id, payload });
            toast.success({ title: 'Request approved', description: 'Invite issued to the requester.' });
            setRequestToApprove(null);
            refetch();
          } catch (err) {
            const description = err instanceof Error ? err.message : 'Unable to approve request.';
            toast.error({ title: 'Approval failed', description });
          }
        }}
      />

      <RejectRequestDialog
        open={Boolean(requestToReject)}
        onOpenChange={(open) => {
          if (!open) setRequestToReject(null);
        }}
        request={requestToReject}
        isSubmitting={rejectMutation.isPending}
        onSubmit={async (payload) => {
          if (!requestToReject) return;
          try {
            await rejectMutation.mutateAsync({ requestId: requestToReject.id, payload });
            toast.success({ title: 'Request rejected', description: 'The requester has been notified.' });
            setRequestToReject(null);
            refetch();
          } catch (err) {
            const description = err instanceof Error ? err.message : 'Unable to reject request.';
            toast.error({ title: 'Rejection failed', description });
          }
        }}
      />
    </div>
  );
}

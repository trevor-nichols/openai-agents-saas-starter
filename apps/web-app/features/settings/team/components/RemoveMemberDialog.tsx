'use client';

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
import type { TeamMemberSummary } from '@/types/team';

interface RemoveMemberDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  member: TeamMemberSummary | null;
  onConfirm: (member: TeamMemberSummary) => Promise<void>;
  isRemoving?: boolean;
}

export function RemoveMemberDialog({
  open,
  onOpenChange,
  member,
  onConfirm,
  isRemoving,
}: RemoveMemberDialogProps) {
  if (!member) {
    return null;
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Remove member?</AlertDialogTitle>
          <AlertDialogDescription>
            {member.email} will immediately lose access to this tenant. This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isRemoving}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={(event) => {
              event.preventDefault();
              void onConfirm(member);
            }}
            disabled={isRemoving}
          >
            {isRemoving ? 'Removing…' : 'Remove member'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

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
import { Textarea } from '@/components/ui/textarea';
import type { ServiceAccountTokenRow } from '@/types/serviceAccounts';

interface RevokeTokenDialogProps {
  token: ServiceAccountTokenRow | null;
  reason: string;
  onReasonChange: (value: string) => void;
  onConfirm: () => void;
  onClose: () => void;
  isSubmitting: boolean;
}

export function RevokeTokenDialog({ token, reason, onReasonChange, onConfirm, onClose, isSubmitting }: RevokeTokenDialogProps) {
  return (
    <AlertDialog open={Boolean(token)} onOpenChange={(open) => { if (!open) onClose(); }}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Revoke {token?.account}</AlertDialogTitle>
          <AlertDialogDescription>
            This immediately invalidates the refresh token. Automation pipelines using it will need a new credential.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div className="space-y-2 py-2">
          <Textarea
            placeholder="Optional reason (shown in audit logs)"
            value={reason}
            onChange={(event) => onReasonChange(event.target.value)}
            disabled={isSubmitting}
          />
        </div>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isSubmitting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            disabled={isSubmitting}
            onClick={onConfirm}
          >
            Revoke token
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

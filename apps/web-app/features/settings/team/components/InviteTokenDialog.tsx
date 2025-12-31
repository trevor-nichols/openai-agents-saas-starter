'use client';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { CopyButton } from '@/components/ui/copy-button';
import { InlineTag } from '@/components/ui/foundation';
import type { TeamInviteIssueResult } from '@/types/team';
import { resolveRoleLabel } from '../utils';

interface InviteTokenDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  invite: TeamInviteIssueResult | null;
}

export function InviteTokenDialog({ open, onOpenChange, invite }: InviteTokenDialogProps) {
  if (!invite) {
    return null;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Invite issued</DialogTitle>
          <DialogDescription>
            Share this invite token with {invite.invite.invitedEmail} to let them join.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium">Role</p>
                <InlineTag tone="default">{resolveRoleLabel(invite.invite.role)}</InlineTag>
              </div>
              <div className="space-y-1 text-right">
                <p className="text-sm font-medium">Token hint</p>
                <p className="text-xs text-foreground/60">{invite.invite.tokenHint}</p>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Invite token
            </label>
            <div className="flex items-center gap-2">
              <Input value={invite.inviteToken} readOnly className="font-mono" />
              <CopyButton content={invite.inviteToken} variant="outline" />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>Done</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

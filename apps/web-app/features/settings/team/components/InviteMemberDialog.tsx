'use client';

import { useEffect, useMemo } from 'react';
import { z } from 'zod';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAuthForm } from '@/hooks/useAuthForm';
import {
  TEAM_ROLE_ORDER,
  type IssueTeamInviteInput,
  type TeamInviteIssueResult,
  type TeamInvitePolicy,
  type TeamRole,
} from '@/types/team';
import { normalizeOptionalString } from '../utils';

const createInviteSchema = (maxHours: number) =>
  z.object({
    invitedEmail: z.string().email('Enter a valid email.'),
    role: z.enum(TEAM_ROLE_ORDER as [TeamRole, ...TeamRole[]], {
      message: 'Select a role.',
    }),
    expiresInHours: z
      .preprocess(normalizeOptionalString, z.coerce.number().int().min(1).max(maxHours).optional())
      .optional(),
  });

interface InviteMemberDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (payload: IssueTeamInviteInput) => Promise<TeamInviteIssueResult>;
  onIssued?: (result: TeamInviteIssueResult) => void;
  isSubmitting?: boolean;
  roleOptions: Array<{ value: TeamRole; label: string; helper?: string }>;
  invitePolicy: TeamInvitePolicy | null;
}

export function InviteMemberDialog({
  open,
  onOpenChange,
  onSubmit,
  onIssued,
  isSubmitting,
  roleOptions,
  invitePolicy,
}: InviteMemberDialogProps) {
  const maxExpiresHours = invitePolicy?.maxExpiresHours ?? 1;
  const defaultExpiresLabel = invitePolicy ? String(invitePolicy.defaultExpiresHours) : '—';
  const inviteSchema = useMemo(() => createInviteSchema(maxExpiresHours), [maxExpiresHours]);
  const { form, onSubmit: handleSubmit } = useAuthForm({
    schema: inviteSchema,
    initialValues: {
      invitedEmail: '',
      role: roleOptions[0]?.value ?? 'member',
      expiresInHours: undefined,
    },
    submitHandler: async (values) => {
      const result = await onSubmit({
        invitedEmail: values.invitedEmail.trim(),
        role: values.role,
        expiresInHours: values.expiresInHours ?? null,
      });
      onIssued?.(result);
      form.reset({
        invitedEmail: '',
        role: roleOptions[0]?.value ?? 'member',
        expiresInHours: undefined,
      });
    },
  });

  useEffect(() => {
    if (open) {
      form.reset({
        invitedEmail: '',
        role: roleOptions[0]?.value ?? 'member',
        expiresInHours: undefined,
      });
    }
  }, [open, form, roleOptions]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Invite a teammate</DialogTitle>
          <DialogDescription>
            Send an invite link to onboard a new teammate with a preset role.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <FormField
              control={form.control}
              name="invitedEmail"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Invitee email</FormLabel>
                  <FormControl>
                    <Input {...field} type="email" placeholder="new@acme.io" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Role</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a role" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {roleOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          <div className="flex flex-col">
                            <span>{option.label}</span>
                            {option.helper ? (
                              <span className="text-xs text-muted-foreground">
                                {option.helper}
                              </span>
                            ) : null}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="expiresInHours"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Expires in (hours)</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      type="number"
                      min={1}
                      max={maxExpiresHours}
                      placeholder={defaultExpiresLabel}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter className="pt-2">
              <Button variant="outline" type="button" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting || !invitePolicy}>
                {isSubmitting ? 'Issuing…' : 'Issue invite'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

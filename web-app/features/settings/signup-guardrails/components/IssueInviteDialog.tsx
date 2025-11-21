'use client';

import { useEffect } from 'react';
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
import { Textarea } from '@/components/ui/textarea';
import { useAuthForm } from '@/hooks/useAuthForm';
import { normalizeOptionalString } from '@/features/settings/signup-guardrails/utils';
import type { IssueSignupInviteInput } from '@/types/signup';

interface IssueInviteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (payload: IssueSignupInviteInput) => Promise<void>;
  isSubmitting?: boolean;
  defaultEmail?: string | null;
  requestId?: string | null;
}

export const issueInviteSchema = z.object({
  invitedEmail: z
    .preprocess(normalizeOptionalString, z.string().email('Enter a valid email.').optional())
    .optional(),
  maxRedemptions: z.coerce.number().int().min(1).max(100).default(1),
  expiresInHours: z
    .preprocess(normalizeOptionalString, z.coerce.number().int().min(1).max(720).optional())
    .optional(),
  note: z.string().max(280, 'Notes must be under 280 characters.').optional(),
});

export function IssueInviteDialog({
  open,
  onOpenChange,
  onSubmit,
  isSubmitting,
  defaultEmail,
  requestId,
}: IssueInviteDialogProps) {
  const { form, onSubmit: handleSubmit } = useAuthForm({
    schema: issueInviteSchema,
    initialValues: {
      invitedEmail: defaultEmail ?? '',
      maxRedemptions: 1,
      expiresInHours: undefined,
      note: '',
    },
    submitHandler: async (values) => {
      await onSubmit({
        invitedEmail: values.invitedEmail?.trim() ?? null,
        maxRedemptions: values.maxRedemptions,
        expiresInHours: values.expiresInHours ?? null,
        note: values.note?.trim() ?? null,
        signupRequestId: requestId ?? null,
      });
      form.reset();
    },
  });

  useEffect(() => {
    if (open) {
      form.reset({
        invitedEmail: defaultEmail ?? '',
        maxRedemptions: 1,
        expiresInHours: undefined,
        note: '',
      });
    }
  }, [defaultEmail, open, form]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Issue signup invite</DialogTitle>
          <DialogDescription>Generate a single- or multi-use token to share with a prospect.</DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <FormField
              control={form.control}
              name="invitedEmail"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email restriction (optional)</FormLabel>
                  <FormControl>
                    <Input {...field} type="email" placeholder="user@company.com" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="maxRedemptions"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Max redemptions</FormLabel>
                  <FormControl>
                    <Input {...field} type="number" min={1} max={100} />
                  </FormControl>
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
                    <Input {...field} type="number" min={1} max={720} placeholder="72" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="note"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Operator note</FormLabel>
                  <FormControl>
                    <Textarea {...field} rows={3} placeholder="Context for this invite." />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter className="pt-2">
              <Button variant="outline" type="button" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Issuing…' : 'Issue invite'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

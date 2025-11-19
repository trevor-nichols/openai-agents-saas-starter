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
import type { SignupRequestSummary } from '@/types/signup';

interface ApproveRequestDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  request?: SignupRequestSummary | null;
  isSubmitting?: boolean;
  onSubmit: (payload: { note?: string | null; inviteExpiresInHours?: number | null }) => Promise<void>;
}

export const approveSchema = z.object({
  note: z.string().max(280, 'Notes must be under 280 characters.').optional(),
  inviteExpiresInHours: z
    .preprocess(normalizeOptionalString, z.coerce.number().int().min(1).max(720).optional())
    .optional(),
});

export function ApproveRequestDialog({ open, onOpenChange, request, isSubmitting, onSubmit }: ApproveRequestDialogProps) {
  const { form, onSubmit: handleSubmit } = useAuthForm({
    schema: approveSchema,
    initialValues: { note: '', inviteExpiresInHours: undefined },
    submitHandler: async (values) => {
      await onSubmit({
        note: values.note?.trim() || null,
        inviteExpiresInHours: values.inviteExpiresInHours ?? null,
      });
      form.reset();
    },
  });

  useEffect(() => {
    if (!open) {
      form.reset();
    }
  }, [open, form]);

  const disabled = !request;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Approve request</DialogTitle>
          <DialogDescription>
            Issue an invite token for {request?.email}. The invite will be attached to the decision record.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <FormField
              control={form.control}
              name="inviteExpiresInHours"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Invite expiry (hours)</FormLabel>
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
                  <FormLabel>Decision note</FormLabel>
                  <FormControl>
                    <Textarea {...field} rows={3} placeholder="Share additional context for your audit log." />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter className="pt-2">
              <Button variant="outline" type="button" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={disabled || isSubmitting}>
                {isSubmitting ? 'Approving…' : 'Approve & issue invite'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

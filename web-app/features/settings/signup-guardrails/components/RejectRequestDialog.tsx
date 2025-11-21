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
import { Textarea } from '@/components/ui/textarea';
import { useAuthForm } from '@/hooks/useAuthForm';
import type { SignupRequestSummary } from '@/types/signup';

interface RejectRequestDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  request?: SignupRequestSummary | null;
  isSubmitting?: boolean;
  onSubmit: (payload: { reason?: string | null }) => Promise<void>;
}

const rejectSchema = z.object({
  reason: z.string().min(4, 'Please provide a short reason.').max(280, 'Keep reasons under 280 characters.'),
});

export function RejectRequestDialog({ open, onOpenChange, request, isSubmitting, onSubmit }: RejectRequestDialogProps) {
  const { form, onSubmit: handleSubmit } = useAuthForm({
    schema: rejectSchema,
    initialValues: { reason: '' },
    submitHandler: async (values) => {
      await onSubmit({ reason: values.reason.trim() });
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
          <DialogTitle>Reject request</DialogTitle>
          <DialogDescription>
            Tell {request?.email} why the access request was denied. The reason is stored in the audit log.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <FormField
              control={form.control}
              name="reason"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Reason</FormLabel>
                  <FormControl>
                    <Textarea {...field} rows={4} placeholder="Provide a short explanation." />
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
                {isSubmitting ? 'Rejecting…' : 'Reject request'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

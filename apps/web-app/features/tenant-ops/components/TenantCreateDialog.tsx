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
import { useAuthForm } from '@/hooks/useAuthForm';
import type { TenantAccountCreateInput } from '@/types/tenantAccount';

import { optionalSlugSchema, tenantNameSchema } from '../forms';

const createTenantSchema = z.object({
  name: tenantNameSchema,
  slug: optionalSlugSchema,
});

interface TenantCreateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (payload: TenantAccountCreateInput) => Promise<void>;
  isSubmitting?: boolean;
}

export function TenantCreateDialog({
  open,
  onOpenChange,
  onSubmit,
  isSubmitting,
}: TenantCreateDialogProps) {
  const { form, onSubmit: handleSubmit } = useAuthForm({
    schema: createTenantSchema,
    initialValues: { name: '', slug: '' },
    submitHandler: async (values) => {
      const payload: TenantAccountCreateInput = {
        name: values.name.trim(),
        slug: values.slug ?? undefined,
      };
      await onSubmit(payload);
      form.reset({ name: '', slug: '' });
    },
  });

  useEffect(() => {
    if (open) {
      form.reset({ name: '', slug: '' });
    }
  }, [open, form]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create tenant</DialogTitle>
          <DialogDescription>
            Create a new tenant for onboarding or operational handoff.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tenant name</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="Acme Corporation" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="slug"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Slug (optional)</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="acme" />
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
                {isSubmitting ? 'Creating…' : 'Create tenant'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

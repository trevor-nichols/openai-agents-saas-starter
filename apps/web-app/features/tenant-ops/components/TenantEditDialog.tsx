'use client';

import { useEffect, useMemo } from 'react';

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
import type { TenantAccountOperatorSummary, TenantAccountUpdateInput } from '@/types/tenantAccount';

import { buildTenantEditSchema } from '../forms';

interface TenantEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tenant: TenantAccountOperatorSummary | null;
  onSubmit: (payload: TenantAccountUpdateInput) => Promise<void>;
  isSubmitting?: boolean;
}

export function TenantEditDialog({
  open,
  onOpenChange,
  tenant,
  onSubmit,
  isSubmitting,
}: TenantEditDialogProps) {
  const editTenantSchema = useMemo(
    () => buildTenantEditSchema(tenant?.slug ?? null),
    [tenant?.slug],
  );
  const { form, onSubmit: handleSubmit } = useAuthForm({
    schema: editTenantSchema,
    initialValues: { name: tenant?.name ?? '', slug: tenant?.slug ?? '' },
    submitHandler: async (values) => {
      if (!tenant) return;
      const name = values.name.trim();
      const rawSlug = values.slug.trim();
      const slug = rawSlug.length > 0 ? rawSlug : undefined;
      const payload: TenantAccountUpdateInput = {};
      if (name && name !== tenant.name) {
        payload.name = name;
      }
      if (slug && slug !== tenant.slug) {
        payload.slug = slug;
      }
      if (Object.keys(payload).length === 0) {
        return;
      }
      await onSubmit(payload);
      form.reset({ name, slug: slug ?? '' });
    },
  });

  useEffect(() => {
    if (open) {
      form.reset({ name: tenant?.name ?? '', slug: tenant?.slug ?? '' });
    }
  }, [open, form, tenant]);

  const nameValue = form.watch('name');
  const slugValue = form.watch('slug');
  const hasChanges = useMemo(() => {
    if (!tenant) return false;
    const trimmedName = (nameValue ?? '').trim();
    const trimmedSlug = (slugValue ?? '').trim();
    return trimmedName !== tenant.name || trimmedSlug !== (tenant.slug ?? '');
  }, [nameValue, slugValue, tenant]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit tenant</DialogTitle>
          <DialogDescription>
            Update the tenant identity details used throughout the platform.
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
                  <FormLabel>Slug</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="acme" />
                  </FormControl>
                  <FormMessage />
                  <p className="text-xs text-foreground/60">
                    Slugs can be updated, but they cannot be cleared once set.
                  </p>
                </FormItem>
              )}
            />

            <DialogFooter className="pt-2">
              <Button variant="outline" type="button" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={!hasChanges || !tenant || isSubmitting}>
                {isSubmitting ? 'Saving…' : 'Save changes'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

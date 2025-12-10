'use client';

import { useEffect } from 'react';
import { useFieldArray, useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { EmptyState } from '@/components/ui/states';
import { useToast } from '@/components/ui/use-toast';
import type { BillingContact } from '@/types/tenantSettings';

import { MAX_BILLING_CONTACTS } from '../constants';
import { createEmptyContact } from '../utils';

const contactSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1, 'Name is required.'),
  email: z.string().email('Enter a valid email.'),
  role: z.string().optional(),
  phone: z.string().optional(),
  notifyBilling: z.boolean(),
});

const contactsSchema = z.object({
  contacts: z
    .array(contactSchema)
    .max(MAX_BILLING_CONTACTS, `Limit ${MAX_BILLING_CONTACTS} contacts.`),
});

type BillingContactsFormValues = z.infer<typeof contactsSchema>;

interface BillingContactsCardProps {
  contacts: BillingContact[];
  isSaving: boolean;
  onSubmit: (nextContacts: BillingContact[]) => Promise<void>;
}

export function BillingContactsCard({ contacts, isSaving, onSubmit }: BillingContactsCardProps) {
  const toast = useToast();
  const toFormValues = (source: BillingContact[]): BillingContactsFormValues => ({
    contacts: source.map((contact) => ({
      id: contact.id,
      name: contact.name,
      email: contact.email,
      role: contact.role ?? '',
      phone: contact.phone ?? '',
      notifyBilling: contact.notifyBilling,
    })),
  });
  const form = useForm<BillingContactsFormValues>({
    resolver: zodResolver(contactsSchema),
    defaultValues: toFormValues(contacts),
  });
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'contacts',
    keyName: 'fieldId',
  });

  useEffect(() => {
    form.reset(toFormValues(contacts));
  }, [contacts, form]);

  const handleSubmit = form.handleSubmit(async (values) => {
    try {
      await onSubmit(
        values.contacts.map((contact) => ({
          id: contact.id,
          name: contact.name.trim(),
          email: contact.email.trim(),
          role: contact.role?.trim() ? contact.role.trim() : null,
          phone: contact.phone?.trim() ? contact.phone.trim() : null,
          notifyBilling: contact.notifyBilling,
        })),
      );
      toast.success({
        title: 'Billing contacts saved',
        description: `${values.contacts.length} contact${values.contacts.length === 1 ? '' : 's'} stored for alerts.`,
      });
      form.reset(values);
    } catch (error) {
      toast.error({
        title: 'Unable to save billing contacts',
        description: error instanceof Error ? error.message : 'Try again shortly.',
      });
    }
  });

  const handleAddContact = () => {
    const empty = createEmptyContact();
    append({
      id: empty.id,
      name: empty.name,
      email: empty.email,
      role: '',
      phone: '',
      notifyBilling: empty.notifyBilling,
    });
  };

  return (
    <GlassPanel className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <SectionHeader
          eyebrow="Billing"
          title="Billing contacts"
          description="We notify these contacts about invoices, usage spikes, and webhook failures."
        />
        <Button
          variant="outline"
          onClick={handleAddContact}
          disabled={fields.length >= MAX_BILLING_CONTACTS}
        >
          Add contact
        </Button>
      </div>
      <Form {...form}>
        <form className="space-y-6" onSubmit={handleSubmit} noValidate>
          <div className="space-y-4">
            {fields.length === 0 ? (
              <EmptyState
                title="No billing contacts yet"
                description="Add at least one person so we know who to alert for billing events."
                action={
                  <Button variant="outline" type="button" onClick={handleAddContact}>
                    Add contact
                  </Button>
                }
              />
            ) : (
              fields.map((field, index) => (
                <div
                  key={field.fieldId}
                  className="rounded-xl border border-white/10 bg-white/5 p-4"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-foreground/80">Contact {index + 1}</p>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => remove(index)}
                    >
                      Remove
                    </Button>
                  </div>
                  <div className="mt-4 grid gap-4 lg:grid-cols-2">
                    <FormField
                      control={form.control}
                      name={`contacts.${index}.name`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Name</FormLabel>
                          <FormControl>
                            <Input {...field} placeholder="Ava Patel" />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name={`contacts.${index}.email`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Email</FormLabel>
                          <FormControl>
                            <Input {...field} type="email" placeholder="ava@example.com" />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name={`contacts.${index}.role`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Role</FormLabel>
                          <FormControl>
                            <Input {...field} placeholder="Finance lead" />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name={`contacts.${index}.phone`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Phone</FormLabel>
                          <FormControl>
                            <Input {...field} placeholder="Optional" />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                  <FormField
                    control={form.control}
                    name={`contacts.${index}.notifyBilling`}
                    render={({ field }) => (
                      <FormItem className="mt-4 flex items-center justify-between rounded-lg border border-white/5 bg-white/5 px-4 py-2">
                        <div>
                          <FormLabel>Send billing alerts</FormLabel>
                          <p className="text-xs text-foreground/60">
                            Receive invoices, usage alerts, and webhook failure notices.
                          </p>
                        </div>
                        <FormControl>
                          <Switch checked={field.value} onCheckedChange={field.onChange} />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                </div>
              ))
            )}
          </div>
          <div className="flex justify-end gap-2">
            <Button type="submit" disabled={isSaving || !form.formState.isDirty}>
              {isSaving ? 'Saving…' : 'Save contacts'}
            </Button>
          </div>
        </form>
      </Form>
    </GlassPanel>
  );
}

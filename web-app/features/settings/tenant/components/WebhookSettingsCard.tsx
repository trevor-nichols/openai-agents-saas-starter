'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
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
import { useToast } from '@/components/ui/use-toast';

const webhookSchema = z.object({
  webhookUrl: z
    .string()
    .url('Enter a valid https URL.')
    .or(z.literal('')),
});

type WebhookFormValues = z.infer<typeof webhookSchema>;

interface WebhookSettingsCardProps {
  webhookUrl: string | null;
  isSaving: boolean;
  onSubmit: (url: string | null) => Promise<void>;
}

export function WebhookSettingsCard({ webhookUrl, isSaving, onSubmit }: WebhookSettingsCardProps) {
  const toast = useToast();
  const form = useForm<WebhookFormValues>({
    resolver: zodResolver(webhookSchema),
    defaultValues: {
      webhookUrl: webhookUrl ?? '',
    },
  });

  useEffect(() => {
    form.reset({ webhookUrl: webhookUrl ?? '' });
  }, [form, webhookUrl]);

  const handleSubmit = form.handleSubmit(async (values) => {
    try {
      await onSubmit(values.webhookUrl.trim() ? values.webhookUrl.trim() : null);
      toast.success({
        title: 'Webhook updated',
        description: values.webhookUrl ? 'We will start delivering billing events to this URL.' : 'Billing webhooks disabled.',
      });
    } catch (error) {
      toast.error({
        title: 'Unable to update webhook',
        description: error instanceof Error ? error.message : 'Try again shortly.',
      });
    }
  });

  return (
    <GlassPanel className="space-y-6">
      <SectionHeader
        eyebrow="Integrations"
        title="Billing webhook URL"
        description="We send invoice events, payment failures, and usage webhooks to this endpoint."
      />
      <Form {...form}>
        <form className="space-y-4" onSubmit={handleSubmit} noValidate>
          <FormField
            control={form.control}
            name="webhookUrl"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Webhook URL</FormLabel>
                <FormControl>
                  <Input {...field} type="url" placeholder="https://hooks.example.com/billing" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => form.reset({ webhookUrl: '' })}
              disabled={isSaving}
            >
              Clear
            </Button>
            <Button type="submit" disabled={isSaving || !form.formState.isDirty}>
              {isSaving ? 'Saving…' : 'Save webhook'}
            </Button>
          </div>
        </form>
      </Form>
    </GlassPanel>
  );
}

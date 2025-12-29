'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { useToast } from '@/components/ui/use-toast';
import type { TenantSubscription } from '@/lib/types/billing';
import { useUpdateSubscriptionMutation } from '@/lib/queries/billingSubscriptions';

import { BILLING_COPY } from '../../shared/constants';
import type { SubscriptionSettingsFormValues } from '../../shared/types';

interface SubscriptionSettingsCardProps {
  tenantId: string | null;
  subscription: TenantSubscription | null;
  isLoading: boolean;
  error?: Error | null;
  onRetry: () => void;
}

export function SubscriptionSettingsCard({
  tenantId,
  subscription,
  isLoading,
  error,
  onRetry,
}: SubscriptionSettingsCardProps) {
  const updateSubscription = useUpdateSubscriptionMutation({ tenantId });
  const { success, error: showError } = useToast();

  const form = useForm<SubscriptionSettingsFormValues>({
    defaultValues: {
      billingEmail: subscription?.billing_email ?? '',
      autoRenew: subscription?.auto_renew ?? true,
      seatCount: subscription?.seat_count ?? undefined,
    },
  });

  useEffect(() => {
    form.reset({
      billingEmail: subscription?.billing_email ?? '',
      autoRenew: subscription?.auto_renew ?? true,
      seatCount: subscription?.seat_count ?? undefined,
    });
  }, [form, subscription?.billing_email, subscription?.auto_renew, subscription?.seat_count]);

  const handleSubmit = async (values: SubscriptionSettingsFormValues) => {
    if (!tenantId) return;
    try {
      await updateSubscription.mutateAsync({
        billing_email: values.billingEmail?.trim() ? values.billingEmail.trim() : null,
        auto_renew: values.autoRenew,
        seat_count: values.seatCount ?? null,
      });
      success({
        title: 'Subscription settings saved',
        description: 'Billing contacts and seat counts are updated.',
      });
    } catch (err) {
      showError({
        title: 'Unable to save settings',
        description: err instanceof Error ? err.message : 'Please try again.',
      });
    }
  };

  if (error) {
    return (
      <GlassPanel>
        <ErrorState
          title="Unable to load subscription settings"
          message="We could not load subscription settings. Refresh the page and try again."
          onRetry={onRetry}
        />
      </GlassPanel>
    );
  }

  if (isLoading) {
    return (
      <GlassPanel>
        <SkeletonPanel lines={4} />
      </GlassPanel>
    );
  }

  if (!subscription) {
    return (
      <GlassPanel>
        <EmptyState
          title="No subscription yet"
          description="Start a subscription to configure billing contacts and seats."
        />
      </GlassPanel>
    );
  }

  return (
    <GlassPanel className="space-y-4">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">
          {BILLING_COPY.planManagement.settings.title}
        </p>
        <p className="text-sm text-foreground/70">
          {BILLING_COPY.planManagement.settings.description}
        </p>
      </div>

      <Form {...form}>
        <form className="space-y-4" onSubmit={form.handleSubmit(handleSubmit)} noValidate>
          <FormField
            control={form.control}
            name="billingEmail"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Billing email</FormLabel>
                <FormDescription>Receives invoices and renewal notices.</FormDescription>
                <FormControl>
                  <Input {...field} type="email" placeholder="billing@example.com" autoComplete="email" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="seatCount"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Seat count</FormLabel>
                <FormDescription>Override included seats for the current plan.</FormDescription>
                <FormControl>
                  <Input
                    {...field}
                    type="number"
                    min={1}
                    placeholder={subscription.seat_count ? String(subscription.seat_count) : 'Leave empty'}
                    value={field.value ?? ''}
                    onChange={(event) => {
                      const parsed = event.target.value ? Number(event.target.value) : undefined;
                      field.onChange(parsed);
                    }}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="autoRenew"
            render={({ field }) => (
              <FormItem className="flex items-center justify-between gap-4">
                <div>
                  <FormLabel>Auto renew</FormLabel>
                  <FormDescription>Keep billing active without manual intervention.</FormDescription>
                </div>
                <FormControl>
                  <Switch checked={field.value} onCheckedChange={(next) => field.onChange(Boolean(next))} />
                </FormControl>
              </FormItem>
            )}
          />

          <Button type="submit" disabled={updateSubscription.isPending}>
            {updateSubscription.isPending
              ? 'Saving…'
              : BILLING_COPY.planManagement.settings.ctaLabel}
          </Button>
        </form>
      </Form>
    </GlassPanel>
  );
}

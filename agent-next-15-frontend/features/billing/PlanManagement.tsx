'use client';

import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';

import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { GlassPanel, InlineTag, KeyValueList, SectionHeader } from '@/components/ui/foundation';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/components/ui/use-toast';
import { useBillingPlans } from '@/lib/queries/billingPlans';
import {
  useStartSubscriptionMutation,
  useTenantSubscription,
} from '@/lib/queries/billingSubscriptions';
import { readClientSessionMeta } from '@/lib/auth/clientMeta';
import type { BillingPlan } from '@/types/billing';

type PlanFormValues = {
  billingEmail: string;
  autoRenew: boolean;
  seatCount?: number;
};

const formatCurrency = (amount: number, currency: string) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount / 100);

function formatInterval(plan: BillingPlan) {
  return plan.interval_count > 1 ? `${plan.interval_count} ${plan.interval}s` : plan.interval;
}

export function PlanManagement() {
  const tenantMeta = useMemo(() => readClientSessionMeta(), []);
  const tenantId = tenantMeta?.tenantId ?? null;
  const [selectedPlan, setSelectedPlan] = useState<BillingPlan | null>(null);

  const { plans, isLoading: isLoadingPlans, error: plansError, refetch: refetchPlans } = useBillingPlans();
  const {
    subscription,
    isLoadingSubscription,
    subscriptionError,
    refetchSubscription,
  } = useTenantSubscription({ tenantId });
  const startSubscription = useStartSubscriptionMutation({ tenantId });
  const toast = useToast();

  const form = useForm<PlanFormValues>({
    defaultValues: {
      billingEmail: subscription?.billing_email ?? '',
      autoRenew: subscription?.auto_renew ?? true,
      seatCount: subscription?.seat_count ?? undefined,
    },
  });

  useEffect(() => {
    if (!selectedPlan) {
      return;
    }

    form.reset({
      billingEmail: subscription?.billing_email ?? '',
      autoRenew: subscription?.auto_renew ?? true,
      seatCount: subscription?.seat_count ?? selectedPlan.seat_included ?? undefined,
    });
  }, [selectedPlan, subscription?.billing_email, subscription?.auto_renew, subscription?.seat_count, form]);

  useEffect(() => {
    if (selectedPlan) {
      startSubscription.reset();
    }
  }, [selectedPlan, startSubscription]);

  const handleSubmit = form.handleSubmit(async (values) => {
    if (!selectedPlan || !tenantId) {
      return;
    }

    try {
      await startSubscription.mutateAsync({
        plan_code: selectedPlan.code,
        billing_email: values.billingEmail || undefined,
        auto_renew: values.autoRenew,
        seat_count: values.seatCount,
      });
      toast.success({
        title: 'Subscription updated',
        description: `You are now on the ${selectedPlan.name} plan.`,
      });
      startSubscription.reset();
      setSelectedPlan(null);
      refetchSubscription();
    } catch (error) {
      toast.error({
        title: 'Plan update failed',
        description: 'Double-check the details and try again.',
      });
      throw error;
    }
  });

  if (!tenantId) {
    return (
      <section className="space-y-8">
        <SectionHeader
          eyebrow="Billing"
          title="Plan management"
          description="Sign in again to access billing controls tied to your tenant."
        />
        <EmptyState
          title="Tenant context missing"
          description="Please refresh or sign back in so we can load your subscription."
        />
      </section>
    );
  }

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow="Billing"
        title="Plan management"
        description="See your current subscription, choose a new plan, and adjust billing contact or seat counts."
      />

      <GlassPanel className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-foreground/60">Current subscription</p>
            <h2 className="text-2xl font-semibold text-foreground">
              {subscription?.plan_code ?? 'No plan found'}
            </h2>
            <p className="text-sm text-foreground/60">
              Status · {subscription?.status ?? 'unknown'}
            </p>
          </div>
          {subscription ? (
            <InlineTag tone={subscription.auto_renew ? 'positive' : 'warning'}>
              Auto renew {subscription.auto_renew ? 'on' : 'off'}
            </InlineTag>
          ) : null}
        </div>
        {subscriptionError ? (
          <ErrorState
            title="Subscription unavailable"
            message="We could not load your current plan. Try refreshing the page."
            onRetry={() => refetchSubscription()}
          />
        ) : isLoadingSubscription ? (
          <SkeletonPanel lines={3} />
        ) : subscription ? (
          <KeyValueList
            columns={2}
            items={[
              { label: 'Plan', value: subscription.plan_code },
              { label: 'Seats', value: subscription.seat_count ?? '—' },
              { label: 'Billing contact', value: subscription.billing_email ?? 'Not set' },
              { label: 'Next billing', value: subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : 'TBD' },
            ]}
          />
        ) : (
          <EmptyState
            title="No subscription detected"
            description="Start a subscription from the plan catalog below."
          />
        )}
      </GlassPanel>

      <GlassPanel className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-foreground">Available plans</p>
            <p className="text-xs text-foreground/60">
              Choose the tier that best fits your team. You can change plans or adjust seats at any time.
            </p>
          </div>
          <InlineTag tone="default">{plans.length} entries</InlineTag>
        </div>

        <div className="space-y-4">
          {isLoadingPlans ? (
            <SkeletonPanel lines={4} />
          ) : plansError ? (
            <ErrorState
              title="Unable to load plans"
              message={plansError ?? 'Something went wrong while fetching billing plans.'}
              onRetry={() => refetchPlans()}
            />
          ) : plans.length === 0 ? (
            <EmptyState title="No plans configured" description="Reach out to platform ops to seed plan data." />
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {plans.map((plan) => {
                const isCurrent = subscription?.plan_code === plan.code;
                const isDisabled = !plan.is_active;
                return (
                  <PlanCard
                    key={plan.code}
                    plan={plan}
                    current={isCurrent}
                    disabled={isDisabled}
                    onSelect={() => setSelectedPlan(plan)}
                  />
                );
              })}
            </div>
          )}
        </div>
      </GlassPanel>

      <Dialog open={Boolean(selectedPlan)} onOpenChange={(open) => !open && setSelectedPlan(null)}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>
              {selectedPlan ? `Switch to the ${selectedPlan.name} plan` : 'Plan change'}
            </DialogTitle>
            <DialogDescription>
              {selectedPlan
                ? `Confirm billing contact, seat count, and auto-renew preferences for the ${selectedPlan.name} tier.`
                : 'Select a plan to see more details.'}
            </DialogDescription>
          </DialogHeader>

          {selectedPlan ? (
            <div className="space-y-6">
              <section className="space-y-2 rounded-2xl border border-white/5 bg-white/5 p-5">
                <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">{selectedPlan.interval}</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-3xl font-semibold text-foreground">{formatCurrency(selectedPlan.price_cents, selectedPlan.currency)}</p>
                  <span className="text-sm text-foreground/60">/ {formatInterval(selectedPlan)}</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedPlan.trial_days ? (
                    <InlineTag tone="default">Trial · {selectedPlan.trial_days}d</InlineTag>
                  ) : null}
                  {selectedPlan.seat_included ? (
                    <InlineTag tone="default">{selectedPlan.seat_included} seats included</InlineTag>
                  ) : null}
                </div>
                {selectedPlan.features?.length ? (
                  <div className="space-y-1 text-sm text-foreground/70">
                    {selectedPlan.features.slice(0, 3).map((feature) => (
                      <p key={feature.key} className="text-foreground/80">
                        <span className="font-semibold">{feature.display_name}:</span>{' '}
                        {feature.description ?? (feature.is_metered ? 'Metered limit' : 'Included')}
                      </p>
                    ))}
                  </div>
                ) : null}
              </section>

              <Form {...form}>
                <form className="space-y-4" onSubmit={handleSubmit} noValidate>
                  <FormField
                    control={form.control}
                    name="billingEmail"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Billing email</FormLabel>
                        <FormDescription>Receives invoices and renewal notices.</FormDescription>
                        <FormControl>
                          <Input
                            {...field}
                            type="email"
                            placeholder="billing@example.com"
                            autoComplete="email"
                          />
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
                        <FormDescription>
                          Override the included seats (omit to rely on the default allocation).
                        </FormDescription>
                        <FormControl>
                          <Input
                            {...field}
                            type="number"
                            min={1}
                            placeholder={selectedPlan.seat_included ? String(selectedPlan.seat_included) : 'Leave empty'}
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
                          <Switch
                            checked={field.value}
                            onCheckedChange={(next) => field.onChange(Boolean(next))}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />

                  {startSubscription.isError ? (
                    <p className="text-sm text-destructive">
                      {(startSubscription.error as Error)?.message ??
                        'Unable to update the subscription.'}
                    </p>
                  ) : null}

                  <DialogFooter className="space-x-3">
                    <Button
                      type="submit"
                      disabled={startSubscription.isPending}
                    >
                      {startSubscription.isPending
                        ? 'Saving...'
                        : subscription?.plan_code === selectedPlan.code
                          ? 'Update plan'
                          : `Move to ${selectedPlan.name}`}
                    </Button>
                    <Button variant="secondary" type="button" onClick={() => setSelectedPlan(null)}>
                      Cancel
                    </Button>
                  </DialogFooter>
                </form>
              </Form>
            </div>
          ) : (
            <SkeletonPanel lines={4} />
          )}
        </DialogContent>
      </Dialog>
    </section>
  );
}

interface PlanCardProps {
  plan: BillingPlan;
  current: boolean;
  disabled: boolean;
  onSelect: () => void;
}

function PlanCard({ plan, current, disabled, onSelect }: PlanCardProps) {
  return (
    <GlassPanel className="flex flex-col justify-between gap-5">
      <div className="space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">{plan.code}</p>
            <h3 className="text-lg font-semibold text-foreground">{plan.name}</h3>
          </div>
          <InlineTag tone={!plan.is_active ? 'warning' : current ? 'positive' : 'default'}>
            {current ? 'Current' : plan.is_active ? 'Active' : 'Retired'}
          </InlineTag>
        </div>
        <div className="flex items-baseline gap-2">
          <p className="text-3xl font-semibold text-foreground">{formatCurrency(plan.price_cents, plan.currency)}</p>
          <span className="text-sm text-foreground/60">/ {formatInterval(plan)}</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {plan.trial_days ? (
            <InlineTag tone="default">Trial {plan.trial_days}d</InlineTag>
          ) : null}
          {plan.seat_included ? (
            <InlineTag tone="default">{plan.seat_included} seats</InlineTag>
          ) : null}
        </div>
        <div className="space-y-1 text-sm text-foreground/70">
          {plan.features?.slice(0, 3).map((feature) => (
            <p key={feature.key}>
              <span className="font-semibold text-foreground">{feature.display_name}</span> –{' '}
              {feature.description ?? (feature.is_metered ? 'Metered' : 'Included')}
            </p>
          ))}
          {!plan.features?.length ? (
            <p className="text-foreground/70">Feature list is coming soon.</p>
          ) : null}
        </div>
      </div>
      <Button
        variant="default"
        disabled={disabled}
        onClick={onSelect}
      >
        {current ? 'Manage this plan' : 'Choose this plan'}
      </Button>
    </GlassPanel>
  );
}

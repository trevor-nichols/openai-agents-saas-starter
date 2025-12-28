'use client';

import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';

import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { SectionHeader } from '@/components/ui/foundation';
import { readClientSessionMeta } from '@/lib/auth/clientMeta';
import { useBillingPlans } from '@/lib/queries/billingPlans';
import {
  useChangeSubscriptionPlanMutation,
  useStartSubscriptionMutation,
  useTenantSubscription,
  useUpdateSubscriptionMutation,
} from '@/lib/queries/billingSubscriptions';
import type { BillingPlan } from '@/types/billing';
import type { SubscriptionUpdatePayload } from '@/lib/types/billing';
import { toast } from 'sonner';

import { BILLING_COPY } from './constants';
import { CurrentSubscriptionCard } from './components/CurrentSubscriptionCard';
import { PlanCard } from './components/PlanCard';
import { PlanChangeDialog } from './components/PlanChangeDialog';
import type { PlanFormValues } from './types';

export function PlanManagement() {
  const tenantMeta = useMemo(() => readClientSessionMeta(), []);
  const tenantId = tenantMeta?.tenantId ?? null;

  const { plans, isLoading: isLoadingPlans, error: plansError, refetch: refetchPlans } = useBillingPlans();
  const {
    subscription,
    isLoadingSubscription,
    subscriptionError,
    refetchSubscription,
  } = useTenantSubscription({ tenantId });
  const startSubscription = useStartSubscriptionMutation({ tenantId });
  const updateSubscription = useUpdateSubscriptionMutation({ tenantId });
  const changePlan = useChangeSubscriptionPlanMutation({ tenantId });

  const [selectedPlan, setSelectedPlan] = useState<BillingPlan | null>(null);

  const hasSubscription = Boolean(subscription);
  const form = useForm<PlanFormValues>({
    defaultValues: {
      billingEmail: subscription?.billing_email ?? '',
      autoRenew: subscription?.auto_renew ?? true,
      seatCount: subscription?.seat_count ?? undefined,
      timing: 'auto',
    },
  });

  useEffect(() => {
    form.reset({
      billingEmail: subscription?.billing_email ?? '',
      autoRenew: subscription?.auto_renew ?? true,
      seatCount: subscription?.seat_count ?? selectedPlan?.seat_included ?? undefined,
      timing: 'auto',
    });
  }, [
    form,
    selectedPlan?.seat_included,
    subscription?.auto_renew,
    subscription?.billing_email,
    subscription?.seat_count,
  ]);

  useEffect(() => {
    if (selectedPlan) {
      startSubscription.reset();
      updateSubscription.reset();
      changePlan.reset();
    }
  }, [changePlan, selectedPlan, startSubscription, updateSubscription]);

  const handlePlanSubmit = async (values: PlanFormValues) => {
    if (!selectedPlan || !tenantId) {
      return;
    }

    try {
      if (!hasSubscription) {
        await startSubscription.mutateAsync({
          plan_code: selectedPlan.code,
          billing_email: values.billingEmail || undefined,
          auto_renew: values.autoRenew,
          seat_count: values.seatCount,
        });
        toast.success('Subscription started', {
          description: `You are now on the ${selectedPlan.name} plan.`,
        });
      } else if (selectedPlan.code === subscription?.plan_code) {
        await updateSubscription.mutateAsync({
          billing_email: values.billingEmail || undefined,
          auto_renew: values.autoRenew,
          seat_count: values.seatCount,
        });
        toast.success('Subscription updated', {
          description: 'Your subscription settings were saved.',
        });
      } else {
        const preferenceUpdates: SubscriptionUpdatePayload = {};
        if (values.billingEmail !== subscription?.billing_email) {
          preferenceUpdates.billing_email = values.billingEmail || undefined;
        }
        if (values.autoRenew !== subscription?.auto_renew) {
          preferenceUpdates.auto_renew = values.autoRenew;
        }
        if (Object.keys(preferenceUpdates).length > 0) {
          await updateSubscription.mutateAsync(preferenceUpdates);
        }

        const planChange = await changePlan.mutateAsync({
          plan_code: selectedPlan.code,
          seat_count: values.seatCount,
          timing: values.timing,
        });
        const effectiveAtLabel = planChange.effective_at
          ? new Date(planChange.effective_at).toLocaleDateString()
          : null;
        if (planChange.timing === 'period_end') {
          toast.success('Plan change scheduled', {
            description: effectiveAtLabel
              ? `Your plan will change on ${effectiveAtLabel}.`
              : 'Your plan will update at the end of the billing period.',
          });
        } else {
          toast.success('Plan updated', {
            description: `You are now on the ${selectedPlan.name} plan.`,
          });
        }
      }
      setSelectedPlan(null);
      startSubscription.reset();
      updateSubscription.reset();
      changePlan.reset();
      refetchSubscription();
    } catch (error) {
      toast.error('Plan update failed', {
        description: error instanceof Error ? error.message : 'Double-check the details and try again.',
      });
      throw error;
    }
  };

  if (!tenantId) {
    return (
      <section className="space-y-8">
        <SectionHeader
          eyebrow={BILLING_COPY.planManagement.eyebrow}
          title={BILLING_COPY.planManagement.title}
          description={BILLING_COPY.planManagement.description}
        />
        <EmptyState
          title={BILLING_COPY.planManagement.emptyTenantTitle}
          description={BILLING_COPY.planManagement.emptyTenantDescription}
        />
      </section>
    );
  }

  const currentPlanCode = subscription?.plan_code ?? null;
  const dialogMode: 'start' | 'update' | 'change' = !hasSubscription
    ? 'start'
    : selectedPlan?.code === currentPlanCode
      ? 'update'
      : 'change';
  const isSubmitting = startSubscription.isPending || updateSubscription.isPending || changePlan.isPending;
  const errorMessage =
    (startSubscription.error as Error)?.message ||
    (updateSubscription.error as Error)?.message ||
    (changePlan.error as Error)?.message;

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow={BILLING_COPY.planManagement.eyebrow}
        title={BILLING_COPY.planManagement.title}
        description={BILLING_COPY.planManagement.description}
      />

      <CurrentSubscriptionCard
        subscription={subscription}
        isLoading={isLoadingSubscription}
        error={subscriptionError}
        onRetry={refetchSubscription}
      />

      <div className="space-y-6">
        <SectionHeader
          eyebrow="Plans"
          title={BILLING_COPY.planManagement.catalogTitle}
          description={BILLING_COPY.planManagement.catalogDescription}
        />
        {isLoadingPlans ? (
          <SkeletonPanel lines={4} />
        ) : plansError ? (
          <ErrorState title="Unable to load plans" message={plansError ?? 'Something went wrong while fetching billing plans.'} onRetry={() => refetchPlans()} />
        ) : plans.length === 0 ? (
          <EmptyState
            title={BILLING_COPY.planManagement.catalogEmptyTitle}
            description={BILLING_COPY.planManagement.catalogEmptyDescription}
          />
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {plans.map((plan) => (
              <PlanCard
                key={plan.code}
                plan={plan}
                current={currentPlanCode === plan.code}
                disabled={!plan.is_active}
                onSelect={() => setSelectedPlan(plan)}
              />
            ))}
          </div>
        )}
      </div>

      <PlanChangeDialog
        open={Boolean(selectedPlan)}
        plan={selectedPlan}
        mode={dialogMode}
        form={form}
        onSubmit={handlePlanSubmit}
        onClose={() => setSelectedPlan(null)}
        isSubmitting={isSubmitting}
        errorMessage={errorMessage}
      />
    </section>
  );
}

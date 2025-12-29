'use client';

import { useEffect, useMemo, useState } from 'react';

import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { SectionHeader } from '@/components/ui/foundation';
import { readClientSessionMeta } from '@/lib/auth/clientMeta';
import { useBillingPlans } from '@/lib/queries/billingPlans';
import {
  useChangeSubscriptionPlanMutation,
  useStartSubscriptionMutation,
  useTenantSubscription,
} from '@/lib/queries/billingSubscriptions';
import type { BillingPlan } from '@/types/billing';
import { useToast } from '@/components/ui/use-toast';

import { BILLING_COPY } from '../shared/constants';
import { CurrentSubscriptionCard } from './components/CurrentSubscriptionCard';
import { BillingPortalCard } from './components/BillingPortalCard';
import { PaymentMethodsPanel } from './components/PaymentMethodsPanel';
import { PlanCard } from './components/PlanCard';
import { PlanChangeDialog } from './components/PlanChangeDialog';
import { SubscriptionSettingsCard } from './components/SubscriptionSettingsCard';
import { UpcomingInvoicePreviewCard } from './components/UpcomingInvoicePreviewCard';
import type { PlanChangeFormValues } from '../shared/types';

export function PlanManagement() {
  const tenantMeta = useMemo(() => readClientSessionMeta(), []);
  const tenantId = tenantMeta?.tenantId ?? null;
  const { success, error: showError } = useToast();

  const { plans, isLoading: isLoadingPlans, error: plansError, refetch: refetchPlans } = useBillingPlans();
  const {
    subscription,
    isLoadingSubscription,
    subscriptionError,
    refetchSubscription,
  } = useTenantSubscription({ tenantId });
  const startSubscription = useStartSubscriptionMutation({ tenantId });
  const changePlan = useChangeSubscriptionPlanMutation({ tenantId });

  const [selectedPlan, setSelectedPlan] = useState<BillingPlan | null>(null);

  useEffect(() => {
    if (selectedPlan) {
      startSubscription.reset();
      changePlan.reset();
    }
  }, [selectedPlan, startSubscription, changePlan]);

  const handlePlanSubmit = async (values: PlanChangeFormValues) => {
    if (!selectedPlan || !tenantId) {
      return;
    }

    try {
      if (subscription) {
        const response = await changePlan.mutateAsync({
          plan_code: selectedPlan.code,
          seat_count: values.seatCount ?? undefined,
          timing: values.timing ?? 'auto',
        });
        const timing = response.timing ?? 'auto';
        const effectiveAtLabel = response.effective_at
          ? new Date(response.effective_at).toLocaleDateString()
          : null;
        const changeLabel =
          timing === 'period_end'
            ? effectiveAtLabel
              ? `Plan change scheduled for ${effectiveAtLabel}.`
              : 'Plan change scheduled for the end of the current period.'
            : 'Plan change will take effect immediately.';
        success({
          title: 'Plan change requested',
          description: changeLabel,
        });
      } else {
        await startSubscription.mutateAsync({
          plan_code: selectedPlan.code,
          billing_email: values.billingEmail?.trim() ? values.billingEmail.trim() : undefined,
          auto_renew: values.autoRenew ?? true,
          seat_count: values.seatCount ?? undefined,
        });
        success({
          title: 'Subscription started',
          description: `You are now on the ${selectedPlan.name} plan.`,
        });
      }
      setSelectedPlan(null);
      startSubscription.reset();
      changePlan.reset();
      refetchSubscription();
    } catch (error) {
      showError({
        title: 'Plan update failed',
        description: error instanceof Error ? error.message : 'Double-check the details and try again.',
      });
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
  const planMutationError = (subscription ? changePlan.error : startSubscription.error) as Error | null;
  const isSubmitting = subscription ? changePlan.isPending : startSubscription.isPending;

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

      <div className="grid gap-6 lg:grid-cols-2">
        <BillingPortalCard tenantId={tenantId} billingEmail={subscription?.billing_email ?? null} />
        <UpcomingInvoicePreviewCard
          tenantId={tenantId}
          seatCount={subscription?.seat_count ?? null}
          enabled={Boolean(subscription)}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SubscriptionSettingsCard
          tenantId={tenantId}
          subscription={subscription ?? null}
          isLoading={isLoadingSubscription}
          error={subscriptionError}
          onRetry={refetchSubscription}
        />
        <PaymentMethodsPanel tenantId={tenantId} billingEmail={subscription?.billing_email ?? null} />
      </div>

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
                disabled={!plan.is_active || (Boolean(subscription) && currentPlanCode === plan.code)}
                onSelect={() => setSelectedPlan(plan)}
              />
            ))}
          </div>
        )}
      </div>

      <PlanChangeDialog
        open={Boolean(selectedPlan)}
        plan={selectedPlan}
        subscription={subscription ?? null}
        onSubmit={handlePlanSubmit}
        onClose={() => setSelectedPlan(null)}
        isSubmitting={isSubmitting}
        errorMessage={planMutationError?.message}
      />
    </section>
  );
}

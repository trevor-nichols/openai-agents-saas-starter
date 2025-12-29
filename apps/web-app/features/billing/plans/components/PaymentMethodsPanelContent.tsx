'use client';

import { useMemo } from 'react';

import { Button } from '@/components/ui/button';
import { InlineTag } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import type { BillingPaymentMethod } from '@/lib/types/billing';

import { BILLING_COPY } from '../../shared/constants';
import { PaymentMethodRow } from './PaymentMethodRow';

interface PaymentMethodsPanelContentProps {
  paymentMethods: BillingPaymentMethod[];
  isLoading: boolean;
  error: string | null;
  onRetry: () => Promise<void>;
  onAdd: () => void;
  onSetDefault: (paymentMethodId: string) => void;
  onRequestDetach: (method: BillingPaymentMethod) => void;
  isAdding: boolean;
  stripeEnabled: boolean;
  canAdd: boolean;
  isSettingDefaultId: string | null;
  isDetachingId: string | null;
}

export function PaymentMethodsPanelContent({
  paymentMethods,
  isLoading,
  error,
  onRetry,
  onAdd,
  onSetDefault,
  onRequestDetach,
  isAdding,
  stripeEnabled,
  canAdd,
  isSettingDefaultId,
  isDetachingId,
}: PaymentMethodsPanelContentProps) {
  const defaultMethod = useMemo(
    () => paymentMethods.find((method) => method.is_default),
    [paymentMethods],
  );

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">
            {BILLING_COPY.planManagement.paymentMethods.title}
          </p>
          <p className="text-sm text-foreground/70">
            {BILLING_COPY.planManagement.paymentMethods.description}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {!stripeEnabled ? <InlineTag tone="warning">Stripe key missing</InlineTag> : null}
          <Button onClick={onAdd} disabled={!stripeEnabled || isAdding || !canAdd}>
            {isAdding ? 'Preparing…' : BILLING_COPY.planManagement.paymentMethods.addLabel}
          </Button>
        </div>
      </div>

      {isLoading ? (
        <SkeletonPanel lines={3} />
      ) : error ? (
        <ErrorState
          title="Unable to load payment methods"
          message={error}
          onRetry={onRetry}
        />
      ) : paymentMethods.length === 0 ? (
        <EmptyState
          title={BILLING_COPY.planManagement.paymentMethods.emptyTitle}
          description={BILLING_COPY.planManagement.paymentMethods.emptyDescription}
        />
      ) : (
        <div className="space-y-3">
          {paymentMethods.map((method) => {
            const canRemove = !method.is_default || paymentMethods.length > 1;

            return (
              <PaymentMethodRow
                key={method.id}
                method={method}
                isSettingDefault={isSettingDefaultId === method.id}
                isDetaching={isDetachingId === method.id}
                canRemove={canRemove}
                onSetDefault={onSetDefault}
                onRequestDetach={onRequestDetach}
              />
            );
          })}

          {defaultMethod ? (
            <p className="text-xs text-foreground/60">
              Default card ·••• {defaultMethod.last4 ?? '—'} is used for renewals.
            </p>
          ) : null}
        </div>
      )}
    </>
  );
}

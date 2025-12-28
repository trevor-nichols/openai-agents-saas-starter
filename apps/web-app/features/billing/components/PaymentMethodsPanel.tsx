'use client';

import { useMemo, useRef, useState } from 'react';
import { CreditCard, MoreHorizontal } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag } from '@/components/ui/foundation';
import { Badge } from '@/components/ui/badge';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { useToast } from '@/components/ui/use-toast';
import type { BillingPaymentMethod } from '@/lib/types/billing';
import { stripeEnabled } from '@/lib/config/stripe';
import {
  useCreateSetupIntentMutation,
  useDetachPaymentMethodMutation,
  usePaymentMethodsQuery,
  useSetDefaultPaymentMethodMutation,
} from '@/lib/queries/billingPaymentMethods';

import { BILLING_COPY } from '../constants';
import { formatCardBrand, formatCardExpiry } from '../utils/formatters';
import { PaymentMethodSetupDialog } from './PaymentMethodSetupDialog';

interface PaymentMethodsPanelProps {
  tenantId: string | null;
  billingEmail?: string | null;
}

export function PaymentMethodsPanel({ tenantId, billingEmail }: PaymentMethodsPanelProps) {
  const { paymentMethods, isLoading, error, refetch } = usePaymentMethodsQuery({ tenantId });
  const createSetupIntent = useCreateSetupIntentMutation({ tenantId });
  const setDefaultMutation = useSetDefaultPaymentMethodMutation({ tenantId });
  const detachMutation = useDetachPaymentMethodMutation({ tenantId });
  const { success, error: showError } = useToast();

  const [setupDialogOpen, setSetupDialogOpen] = useState(false);
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [pendingDetach, setPendingDetach] = useState<BillingPaymentMethod | null>(null);
  const setupRequestIdRef = useRef(0);

  const isAdding = createSetupIntent.isPending;
  const activeDefaultMutation = setDefaultMutation.isPending
    ? (setDefaultMutation.variables?.paymentMethodId ?? null)
    : null;
  const activeDetachMutation = detachMutation.isPending
    ? (detachMutation.variables?.paymentMethodId ?? null)
    : null;

  const invalidateSetupIntent = () => {
    setupRequestIdRef.current += 1;
    setClientSecret(null);
  };

  const handleAddPaymentMethod = async () => {
    if (!stripeEnabled) {
      showError({
        title: 'Stripe key missing',
        description: 'Set NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY to enable card entry.',
      });
      return;
    }
    if (!tenantId) {
      return;
    }

    invalidateSetupIntent();
    const requestId = setupRequestIdRef.current;
    setSetupDialogOpen(true);
    try {
      const intent = await createSetupIntent.mutateAsync({
        billing_email: billingEmail ?? undefined,
      });
      if (setupRequestIdRef.current !== requestId) {
        return;
      }
      const secret = intent.client_secret ?? null;
      if (!secret) {
        throw new Error('Stripe did not return a client secret.');
      }
      setClientSecret(secret);
    } catch (err) {
      if (setupRequestIdRef.current !== requestId) {
        return;
      }
      showError({
        title: 'Unable to start setup',
        description: err instanceof Error ? err.message : 'Please try again.',
      });
      setSetupDialogOpen(false);
    }
  };

  const handleSetupComplete = () => {
    invalidateSetupIntent();
    setSetupDialogOpen(false);
    refetch();
  };

  const handleSetDefault = async (paymentMethodId: string) => {
    try {
      await setDefaultMutation.mutateAsync({ paymentMethodId });
      success({ title: 'Default payment method updated' });
    } catch (err) {
      showError({
        title: 'Unable to update default',
        description: err instanceof Error ? err.message : 'Please try again.',
      });
    }
  };

  const handleDetach = async () => {
    if (!pendingDetach) return;
    try {
      await detachMutation.mutateAsync({ paymentMethodId: pendingDetach.id });
      success({ title: 'Payment method removed' });
      setPendingDetach(null);
    } catch (err) {
      showError({
        title: 'Unable to remove payment method',
        description: err instanceof Error ? err.message : 'Please try again.',
      });
    }
  };

  return (
    <GlassPanel className="space-y-4">
      <PaymentMethodsPanelContent
        paymentMethods={paymentMethods}
        isLoading={isLoading}
        error={error}
        onRetry={refetch}
        onAdd={handleAddPaymentMethod}
        onSetDefault={handleSetDefault}
        onRequestDetach={setPendingDetach}
        isAdding={isAdding}
        stripeEnabled={stripeEnabled}
        canAdd={Boolean(tenantId)}
        isSettingDefaultId={activeDefaultMutation}
        isDetachingId={activeDetachMutation}
      />

      <PaymentMethodSetupDialog
        open={setupDialogOpen}
        onOpenChange={(next) => {
          if (!next) {
            invalidateSetupIntent();
          }
          setSetupDialogOpen(next);
        }}
        clientSecret={clientSecret}
        isLoading={createSetupIntent.isPending && !clientSecret}
        billingEmail={billingEmail}
        onComplete={handleSetupComplete}
      />

      <AlertDialog open={Boolean(pendingDetach)} onOpenChange={(open) => !open && setPendingDetach(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove payment method?</AlertDialogTitle>
            <AlertDialogDescription>
              This card will no longer be available for invoice payments.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setPendingDetach(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDetach}>
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </GlassPanel>
  );
}

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
            const isDefault = Boolean(method.is_default);
            const isBusyDefault = isSettingDefaultId === method.id;
            const isBusyDetach = isDetachingId === method.id;
            const canRemove = !isDefault || paymentMethods.length > 1;

            return (
              <div
                key={method.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/5 bg-white/5 p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10">
                    <CreditCard className="h-5 w-5 text-foreground/70" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-foreground">
                      {formatCardBrand(method.brand)} ·••• {method.last4 ?? '—'}
                    </p>
                    <p className="text-xs text-foreground/60">
                      Expires {formatCardExpiry(method.exp_month, method.exp_year)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {isDefault ? <Badge variant="secondary">Default</Badge> : null}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" aria-label="Payment method actions">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        disabled={isDefault || isBusyDefault}
                        onClick={() => onSetDefault(method.id)}
                      >
                        {isBusyDefault ? 'Updating…' : 'Make default'}
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        disabled={!canRemove || isBusyDetach}
                        onClick={() => onRequestDetach(method)}
                      >
                        {isBusyDetach ? 'Removing…' : 'Remove'}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
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

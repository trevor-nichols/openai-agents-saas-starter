import { useCallback, useRef, useState } from 'react';

import { useToast } from '@/components/ui/use-toast';
import { stripeEnabled } from '@/lib/config/stripe';
import type { BillingPaymentMethod } from '@/lib/types/billing';
import {
  useCreateSetupIntentMutation,
  useDetachPaymentMethodMutation,
  usePaymentMethodsQuery,
  useSetDefaultPaymentMethodMutation,
} from '@/lib/queries/billingPaymentMethods';

interface UsePaymentMethodsPanelOptions {
  tenantId: string | null;
  billingEmail?: string | null;
}

export function usePaymentMethodsPanel({ tenantId, billingEmail }: UsePaymentMethodsPanelOptions) {
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
  const isSettingDefaultId = setDefaultMutation.isPending
    ? (setDefaultMutation.variables?.paymentMethodId ?? null)
    : null;
  const isDetachingId = detachMutation.isPending
    ? (detachMutation.variables?.paymentMethodId ?? null)
    : null;

  const invalidateSetupIntent = useCallback(() => {
    setupRequestIdRef.current += 1;
    setClientSecret(null);
  }, []);

  const handleAddPaymentMethod = useCallback(async () => {
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
  }, [billingEmail, createSetupIntent, invalidateSetupIntent, showError, tenantId]);

  const handleSetupComplete = useCallback(() => {
    invalidateSetupIntent();
    setSetupDialogOpen(false);
    refetch();
  }, [invalidateSetupIntent, refetch]);

  const handleSetupDialogOpenChange = useCallback(
    (next: boolean) => {
      if (!next) {
        invalidateSetupIntent();
      }
      setSetupDialogOpen(next);
    },
    [invalidateSetupIntent],
  );

  const handleSetDefault = useCallback(
    async (paymentMethodId: string) => {
      try {
        await setDefaultMutation.mutateAsync({ paymentMethodId });
        success({ title: 'Default payment method updated' });
      } catch (err) {
        showError({
          title: 'Unable to update default',
          description: err instanceof Error ? err.message : 'Please try again.',
        });
      }
    },
    [setDefaultMutation, showError, success],
  );

  const handleDetach = useCallback(async () => {
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
  }, [detachMutation, pendingDetach, showError, success]);

  return {
    paymentMethods,
    isLoading,
    error,
    refetch,
    isAdding,
    stripeEnabled,
    canAdd: Boolean(tenantId),
    setupDialogOpen,
    clientSecret,
    pendingDetach,
    setPendingDetach,
    isSettingDefaultId,
    isDetachingId,
    isDetaching: detachMutation.isPending,
    onAdd: handleAddPaymentMethod,
    onSetDefault: handleSetDefault,
    onConfirmDetach: handleDetach,
    onSetupComplete: handleSetupComplete,
    onSetupDialogOpenChange: handleSetupDialogOpenChange,
  };
}

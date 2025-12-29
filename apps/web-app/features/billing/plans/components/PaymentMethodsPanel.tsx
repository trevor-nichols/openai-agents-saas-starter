'use client';

import { GlassPanel } from '@/components/ui/foundation';

import { PaymentMethodRemoveDialog } from './PaymentMethodRemoveDialog';
import { PaymentMethodSetupDialog } from './PaymentMethodSetupDialog';
import { PaymentMethodsPanelContent } from './PaymentMethodsPanelContent';
import { usePaymentMethodsPanel } from '../hooks/usePaymentMethodsPanel';

interface PaymentMethodsPanelProps {
  tenantId: string | null;
  billingEmail?: string | null;
}

export function PaymentMethodsPanel({ tenantId, billingEmail }: PaymentMethodsPanelProps) {
  const {
    paymentMethods,
    isLoading,
    error,
    refetch,
    isAdding,
    stripeEnabled,
    canAdd,
    setupDialogOpen,
    clientSecret,
    pendingDetach,
    setPendingDetach,
    isSettingDefaultId,
    isDetachingId,
    isDetaching,
    onAdd,
    onSetDefault,
    onConfirmDetach,
    onSetupComplete,
    onSetupDialogOpenChange,
  } = usePaymentMethodsPanel({ tenantId, billingEmail });

  return (
    <GlassPanel className="space-y-4">
      <PaymentMethodsPanelContent
        paymentMethods={paymentMethods}
        isLoading={isLoading}
        error={error}
        onRetry={refetch}
        onAdd={onAdd}
        onSetDefault={onSetDefault}
        onRequestDetach={setPendingDetach}
        isAdding={isAdding}
        stripeEnabled={stripeEnabled}
        canAdd={canAdd}
        isSettingDefaultId={isSettingDefaultId}
        isDetachingId={isDetachingId}
      />

      <PaymentMethodSetupDialog
        open={setupDialogOpen}
        onOpenChange={onSetupDialogOpenChange}
        clientSecret={clientSecret}
        isLoading={isAdding && !clientSecret}
        billingEmail={billingEmail}
        onComplete={onSetupComplete}
      />

      <PaymentMethodRemoveDialog
        open={Boolean(pendingDetach)}
        onOpenChange={(open) => !open && setPendingDetach(null)}
        onConfirm={onConfirmDetach}
        isLoading={isDetaching}
      />
    </GlassPanel>
  );
}

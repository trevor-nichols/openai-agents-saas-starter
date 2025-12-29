'use client';

import { useMemo, useState, type FormEvent } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, PaymentElement, useElements, useStripe } from '@stripe/react-stripe-js';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { SkeletonPanel } from '@/components/ui/states';
import { useToast } from '@/components/ui/use-toast';
import { stripePublishableKey } from '@/lib/config/stripe';

const stripePromise = stripePublishableKey ? loadStripe(stripePublishableKey) : null;

interface PaymentMethodSetupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clientSecret: string | null;
  isLoading: boolean;
  billingEmail?: string | null;
  onComplete: () => void;
}

export function PaymentMethodSetupDialog({
  open,
  onOpenChange,
  clientSecret,
  isLoading,
  billingEmail,
  onComplete,
}: PaymentMethodSetupDialogProps) {
  const showStripeUnavailable = !stripePromise;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Add a payment method</DialogTitle>
          <DialogDescription>
            Securely add a card for upcoming invoices and plan changes.
          </DialogDescription>
        </DialogHeader>

        {showStripeUnavailable ? (
          <p className="text-sm text-muted-foreground">
            Stripe Elements is unavailable. Add NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY to enable card entry.
          </p>
        ) : isLoading ? (
          <SkeletonPanel lines={3} />
        ) : clientSecret ? (
          <Elements
            stripe={stripePromise}
            options={{
              clientSecret,
              appearance: {
                theme: 'night',
              },
            }}
          >
            <SetupIntentForm
              billingEmail={billingEmail}
              onComplete={onComplete}
              onCancel={() => onOpenChange(false)}
            />
          </Elements>
        ) : (
          <p className="text-sm text-muted-foreground">Unable to start setup. Please retry.</p>
        )}
      </DialogContent>
    </Dialog>
  );
}

interface SetupIntentFormProps {
  billingEmail?: string | null;
  onComplete: () => void;
  onCancel: () => void;
}

function SetupIntentForm({ billingEmail, onComplete, onCancel }: SetupIntentFormProps) {
  const stripe = useStripe();
  const elements = useElements();
  const { success, error } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const confirmParams = useMemo(
    () => ({
      payment_method_data: billingEmail
        ? {
            billing_details: {
              email: billingEmail,
            },
          }
        : undefined,
      return_url: typeof window !== 'undefined' ? window.location.href : undefined,
    }),
    [billingEmail],
  );

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!stripe || !elements) {
      return;
    }
    setIsSubmitting(true);
    const { error: stripeError } = await stripe.confirmSetup({
      elements,
      confirmParams,
      redirect: 'if_required',
    });

    if (stripeError) {
      error({ title: 'Card setup failed', description: stripeError.message });
      setIsSubmitting(false);
      return;
    }

    success({ title: 'Payment method added', description: 'Your default card list will refresh shortly.' });
    setIsSubmitting(false);
    onComplete();
  };

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <PaymentElement />
      <DialogFooter className="gap-3 sm:justify-end">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting || !stripe || !elements}>
          {isSubmitting ? 'Saving…' : 'Save payment method'}
        </Button>
      </DialogFooter>
    </form>
  );
}

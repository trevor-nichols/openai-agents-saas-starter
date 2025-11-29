import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { InlineTag } from '@/components/ui/foundation';
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { SkeletonPanel } from '@/components/ui/states';
import type { PlanFormValues } from '@/features/billing/types';
import type { BillingPlan } from '@/types/billing';
import type { UseFormReturn } from 'react-hook-form';

import { formatCurrency, formatInterval } from '../utils/formatters';

interface PlanChangeDialogProps {
  open: boolean;
  plan: BillingPlan | null;
  form: UseFormReturn<PlanFormValues>;
  onSubmit: (values: PlanFormValues) => void;
  onClose: () => void;
  isSubmitting: boolean;
  errorMessage?: string;
  isUpdatingCurrentPlan: boolean;
}

export function PlanChangeDialog({
  open,
  plan,
  form,
  onSubmit,
  onClose,
  isSubmitting,
  errorMessage,
  isUpdatingCurrentPlan,
}: PlanChangeDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>{plan ? `Switch to the ${plan.name} plan` : 'Plan change'}</DialogTitle>
          <DialogDescription>
            {plan
              ? `Confirm billing contact, seat count, and auto-renew preferences for the ${plan.name} tier.`
              : 'Select a plan to see more details.'}
          </DialogDescription>
        </DialogHeader>

        {plan ? (
          <div className="space-y-6">
            <section className="space-y-2 rounded-2xl border border-white/5 bg-white/5 p-5">
              <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">{plan.interval}</p>
              <div className="flex items-baseline gap-2">
                <p className="text-3xl font-semibold text-foreground">{formatCurrency(plan.price_cents, plan.currency)}</p>
                <span className="text-sm text-foreground/60">/ {formatInterval(plan)}</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {plan.trial_days ? <InlineTag tone="default">Trial · {plan.trial_days}d</InlineTag> : null}
                {plan.seat_included ? <InlineTag tone="default">{plan.seat_included} seats included</InlineTag> : null}
              </div>
              {plan.features?.length ? (
                <div className="space-y-1 text-sm text-foreground/70">
                  {plan.features.slice(0, 3).map((feature) => (
                    <p key={feature.key} className="text-foreground/80">
                      <span className="font-semibold">{feature.display_name}:</span>{' '}
                      {feature.description ?? (feature.is_metered ? 'Metered limit' : 'Included')}
                    </p>
                  ))}
                </div>
              ) : null}
            </section>

            <Form {...form}>
              <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)} noValidate>
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
                      <FormDescription>Override the included seats (omit to rely on the default allocation).</FormDescription>
                      <FormControl>
                        <Input
                          {...field}
                          type="number"
                          min={1}
                          placeholder={plan.seat_included ? String(plan.seat_included) : 'Leave empty'}
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

                {errorMessage ? <p className="text-sm text-destructive">{errorMessage}</p> : null}

                <DialogFooter className="space-x-3">
                  <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting
                      ? 'Saving...'
                      : isUpdatingCurrentPlan
                        ? 'Update plan'
                        : `Move to ${plan.name}`}
                  </Button>
                  <Button variant="secondary" type="button" onClick={onClose} disabled={isSubmitting}>
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
  );
}

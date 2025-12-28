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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { SkeletonPanel } from '@/components/ui/states';
import type { PlanFormValues } from '@/features/billing/types';
import type { BillingPlan } from '@/types/billing';
import type { UseFormReturn } from 'react-hook-form';

import { formatCurrency, formatInterval } from '../utils/formatters';

interface PlanChangeDialogProps {
  open: boolean;
  plan: BillingPlan | null;
  mode: 'start' | 'update' | 'change';
  form: UseFormReturn<PlanFormValues>;
  onSubmit: (values: PlanFormValues) => void;
  onClose: () => void;
  isSubmitting: boolean;
  errorMessage?: string;
}

export function PlanChangeDialog({
  open,
  plan,
  mode,
  form,
  onSubmit,
  onClose,
  isSubmitting,
  errorMessage,
}: PlanChangeDialogProps) {
  const title = plan
    ? mode === 'start'
      ? `Start the ${plan.name} plan`
      : mode === 'update'
        ? `Update ${plan.name} subscription`
        : `Switch to the ${plan.name} plan`
    : 'Plan change';

  const description = plan
    ? mode === 'change'
      ? `Choose seats and timing for moving to the ${plan.name} tier.`
      : `Confirm billing contact, seat count, and auto-renew preferences for the ${plan.name} tier.`
    : 'Select a plan to see more details.';

  const submitLabel = plan
    ? mode === 'start'
      ? `Start ${plan.name}`
      : mode === 'update'
        ? 'Update subscription'
        : `Request ${plan.name} plan`
    : 'Submit';

  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
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

                {mode === 'change' ? (
                  <FormField
                    control={form.control}
                    name="timing"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Plan change timing</FormLabel>
                        <FormDescription>
                          Auto applies upgrades immediately and schedules downgrades for period end.
                        </FormDescription>
                        <Select value={field.value} onValueChange={field.onChange}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select timing" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="auto">Auto (recommended)</SelectItem>
                            <SelectItem value="immediate">Immediate</SelectItem>
                            <SelectItem value="period_end">At period end</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                ) : null}

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
                    {isSubmitting ? 'Saving...' : submitLabel}
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

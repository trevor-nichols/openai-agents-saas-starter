import { SectionHeader } from '@/components/ui/foundation';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

import type { FeatureComparisonRow } from '../types';
import type { BillingPlan } from '@/types/billing';

interface PlanComparisonTableProps {
  plans: BillingPlan[];
  rows: FeatureComparisonRow[];
}

export function PlanComparisonTable({ plans, rows }: PlanComparisonTableProps) {
  if (!rows.length || !plans.length) {
    return null;
  }

  return (
    <section className="space-y-6">
      <SectionHeader
        eyebrow="Comparison"
        title="Feature coverage by tier"
        description="Inspect exactly how plans differ so you can pick the right tier for your launch."
      />
      <ScrollArea className="rounded-2xl border border-white/10">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Feature</TableHead>
              {plans.map((plan) => (
                <TableHead key={plan.code} className="text-right">
                  {plan.name}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.featureKey}>
                <TableCell>
                  <div>
                    <p className="font-semibold text-foreground">{row.label}</p>
                    {row.description ? (
                      <p className="text-sm text-foreground/60">{row.description}</p>
                    ) : null}
                  </div>
                </TableCell>
                {plans.map((plan) => (
                  <TableCell key={`${row.featureKey}-${plan.code}`} className="text-right text-sm text-foreground/70">
                    {row.availability[plan.code] ?? '—'}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </ScrollArea>
    </section>
  );
}

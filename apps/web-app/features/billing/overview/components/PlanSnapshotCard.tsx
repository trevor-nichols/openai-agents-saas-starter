import Link from 'next/link';
import { CreditCard, CalendarRange } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { InlineTag } from '@/components/ui/foundation';
import { BILLING_COPY } from '@/features/billing/shared/constants';
import type { PlanSnapshot } from '@/features/billing/shared/types';

interface PlanSnapshotCardProps {
  snapshot: PlanSnapshot;
}

export function PlanSnapshotCard({ snapshot }: PlanSnapshotCardProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">Current Plan</CardTitle>
        <CreditCard className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent className="flex-1 space-y-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold">{snapshot.planCode}</span>
            <InlineTag tone={snapshot.statusTone} className="h-5">
              {snapshot.statusLabel}
            </InlineTag>
          </div>
          <p className="text-xs text-muted-foreground">
            Renews {snapshot.autoRenewLabel.toLowerCase()}
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-foreground/80">
          <CalendarRange className="h-3.5 w-3.5 text-muted-foreground" />
          <span>{snapshot.currentPeriodLabel}</span>
        </div>
      </CardContent>
      <CardFooter>
        <Button asChild size="sm" variant="outline" className="w-full">
          <Link href="/billing/plans">{BILLING_COPY.overview.subscribeLabel}</Link>
        </Button>
      </CardFooter>
    </Card>
  );
}

import { Activity, Users } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { InlineTag } from '@/components/ui/foundation';
import type { PlanSnapshot } from '@/features/billing/types';
import type { BillingStreamStatus } from '@/types/billing';

import { formatStatusLabel } from '../utils/formatters';

interface BillingHealthCardProps {
  snapshot: PlanSnapshot;
  streamStatus: BillingStreamStatus;
}

export function BillingHealthCard({ snapshot, streamStatus }: BillingHealthCardProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">System Health</CardTitle>
        <Activity className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent className="flex flex-1 flex-col justify-between gap-4">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-2xl font-bold">{snapshot.seatCount}</span>
              <p className="text-xs text-muted-foreground">Active seats</p>
            </div>
            <Users className="h-8 w-8 opacity-10" />
          </div>
          
          <div className="flex items-center justify-between border-t pt-4">
            <div className="space-y-1">
              <span className="text-sm font-medium">Billing Stream</span>
              <p className="text-xs text-muted-foreground">Realtime events</p>
            </div>
            <InlineTag tone={streamStatus === 'error' ? 'warning' : 'positive'}>
              {formatStatusLabel(streamStatus)}
            </InlineTag>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

'use client';

import type { BillingEventProcessingStatus } from '@/types/billing';

import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const STATUS_OPTIONS: Array<{ value: BillingEventProcessingStatus | 'all'; label: string }>
  = [
    { value: 'all', label: 'All statuses' },
    { value: 'received', label: 'Received (pending)' },
    { value: 'processed', label: 'Processed' },
    { value: 'failed', label: 'Failed' },
  ];

interface BillingEventFiltersProps {
  processingStatus: BillingEventProcessingStatus | 'all';
  onProcessingStatusChange: (value: BillingEventProcessingStatus | 'all') => void;
  eventType: string;
  onEventTypeChange: (value: string) => void;
}

export function BillingEventFilters({
  processingStatus,
  onProcessingStatusChange,
  eventType,
  onEventTypeChange,
}: BillingEventFiltersProps) {
  return (
    <div className="flex flex-wrap gap-6">
      <div className="flex min-w-[200px] flex-col gap-2">
        <Label htmlFor="billing-status-filter">Processing status</Label>
        <Select
          value={processingStatus}
          onValueChange={(value) =>
            onProcessingStatusChange(value as BillingEventProcessingStatus | 'all')
          }
        >
          <SelectTrigger id="billing-status-filter" className="w-[220px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            {STATUS_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex min-w-[240px] flex-col gap-2">
        <Label htmlFor="billing-event-type-filter">Event type</Label>
        <Input
          id="billing-event-type-filter"
          placeholder="stripe.event.type"
          value={eventType}
          onChange={(event) => onEventTypeChange(event.target.value)}
        />
      </div>
    </div>
  );
}

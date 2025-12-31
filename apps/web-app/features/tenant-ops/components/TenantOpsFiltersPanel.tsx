'use client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

import { TENANT_STATUS_OPTIONS, type TenantStatusFilter } from '../constants';

interface TenantOpsFiltersPanelProps {
  status: TenantStatusFilter;
  query: string;
  isLoading: boolean;
  onStatusChange: (value: TenantStatusFilter) => void;
  onQueryChange: (value: string) => void;
  onApply: () => void;
  onReset: () => void;
}

export function TenantOpsFiltersPanel({
  status,
  query,
  isLoading,
  onStatusChange,
  onQueryChange,
  onApply,
  onReset,
}: TenantOpsFiltersPanelProps) {
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div className="grid gap-4 md:grid-cols-[200px_minmax(240px,_1fr)]">
        <div className="space-y-2">
          <label className="text-xs uppercase tracking-[0.2em] text-foreground/50">Status</label>
          <Select value={status} onValueChange={(value) => onStatusChange(value as TenantStatusFilter)}>
            <SelectTrigger>
              <SelectValue placeholder="Select status" />
            </SelectTrigger>
            <SelectContent>
              {TENANT_STATUS_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <label className="text-xs uppercase tracking-[0.2em] text-foreground/50">Search</label>
          <Input
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Search tenant name or slug"
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button type="button" variant="outline" onClick={onReset} disabled={isLoading}>
          Reset
        </Button>
        <Button type="button" onClick={onApply} disabled={isLoading}>
          {isLoading ? 'Refreshing…' : 'Apply filters'}
        </Button>
      </div>
    </div>
  );
}

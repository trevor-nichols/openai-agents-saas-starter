'use client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { GlassPanel } from '@/components/ui/foundation';

import {
  CHANNEL_FILTER_OPTIONS,
  SEVERITY_FILTER_OPTIONS,
  STATUS_FILTER_OPTIONS,
  type ChannelFilter,
  type SeverityFilter,
  type StatusFilter,
} from '../constants';

interface StatusOpsFiltersPanelProps {
  channelFilter: ChannelFilter;
  statusFilter: StatusFilter;
  severityFilter: SeverityFilter;
  searchTerm: string;
  tenantInput: string;
  appliedTenantId: string | null;
  onChannelChange: (value: ChannelFilter) => void;
  onStatusChange: (value: StatusFilter) => void;
  onSeverityChange: (value: SeverityFilter) => void;
  onSearchTermChange: (value: string) => void;
  onTenantInputChange: (value: string) => void;
  onApplyTenantFilter: () => void;
  onClearTenantFilter: () => void;
  onResetFilters: () => void;
}

export function StatusOpsFiltersPanel({
  channelFilter,
  statusFilter,
  severityFilter,
  searchTerm,
  tenantInput,
  appliedTenantId,
  onChannelChange,
  onStatusChange,
  onSeverityChange,
  onSearchTermChange,
  onTenantInputChange,
  onApplyTenantFilter,
  onClearTenantFilter,
  onResetFilters,
}: StatusOpsFiltersPanelProps) {
  return (
    <GlassPanel className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Select value={channelFilter} onValueChange={(value) => onChannelChange(value as ChannelFilter)}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Channel" />
          </SelectTrigger>
          <SelectContent>
            {CHANNEL_FILTER_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={statusFilter} onValueChange={(value) => onStatusChange(value as StatusFilter)}>
          <SelectTrigger className="w-[170px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            {STATUS_FILTER_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={severityFilter} onValueChange={(value) => onSeverityChange(value as SeverityFilter)}>
          <SelectTrigger className="w-[170px]">
            <SelectValue placeholder="Severity" />
          </SelectTrigger>
          <SelectContent>
            {SEVERITY_FILTER_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Input
          className="min-w-[200px] flex-1"
          placeholder="Search subscriber or creator"
          value={searchTerm}
          onChange={(event) => onSearchTermChange(event.target.value)}
        />
      </div>

      <div className="flex flex-wrap items-end gap-2">
        <div className="flex flex-col gap-2">
          <Label htmlFor="tenant-filter">Tenant filter</Label>
          <div className="flex gap-2">
            <Input
              id="tenant-filter"
              placeholder="Tenant UUID (optional)"
              value={tenantInput}
              onChange={(event) => onTenantInputChange(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') onApplyTenantFilter();
              }}
            />
            <Button variant="outline" onClick={onApplyTenantFilter}>
              Apply
            </Button>
            {appliedTenantId ? (
              <Button variant="ghost" onClick={onClearTenantFilter}>
                Clear
              </Button>
            ) : null}
          </div>
        </div>

        <Button variant="ghost" onClick={onResetFilters}>
          Reset filters
        </Button>
      </div>
    </GlassPanel>
  );
}

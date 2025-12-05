'use client';

import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { ServiceAccountStatusFilter } from '@/types/serviceAccounts';

import { SERVICE_ACCOUNT_STATUS_OPTIONS } from '../constants';

interface ServiceAccountFiltersProps {
  accountSearch: string;
  status: ServiceAccountStatusFilter;
  onAccountSearchChange: (value: string) => void;
  onStatusChange: (value: ServiceAccountStatusFilter) => void;
}

export function ServiceAccountFilters({
  accountSearch,
  status,
  onAccountSearchChange,
  onStatusChange,
}: ServiceAccountFiltersProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <Input
        className="w-full max-w-xs"
        placeholder="Search account"
        value={accountSearch}
        onChange={(event) => onAccountSearchChange(event.target.value)}
      />
      <Select value={status} onValueChange={(value) => onStatusChange(value as ServiceAccountStatusFilter)}>
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          {SERVICE_ACCOUNT_STATUS_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

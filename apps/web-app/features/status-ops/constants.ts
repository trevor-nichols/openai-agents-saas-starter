export type ChannelFilter = 'all' | 'email' | 'webhook';
export type StatusFilter = 'all' | 'active' | 'pending_verification' | 'revoked';
export type SeverityFilter = 'any' | 'all' | 'major' | 'maintenance';
export type DispatchSeverity = 'all' | 'major' | 'maintenance';

interface FilterOption<T extends string> {
  value: T;
  label: string;
}

export const CHANNEL_FILTER_OPTIONS: FilterOption<ChannelFilter>[] = [
  { value: 'all', label: 'All channels' },
  { value: 'email', label: 'Email' },
  { value: 'webhook', label: 'Webhook' },
];

export const STATUS_FILTER_OPTIONS: FilterOption<StatusFilter>[] = [
  { value: 'all', label: 'All statuses' },
  { value: 'active', label: 'Active' },
  { value: 'pending_verification', label: 'Pending verification' },
  { value: 'revoked', label: 'Revoked' },
];

export const SEVERITY_FILTER_OPTIONS: FilterOption<SeverityFilter>[] = [
  { value: 'any', label: 'Any severity' },
  { value: 'major', label: 'Major' },
  { value: 'maintenance', label: 'Maintenance' },
  { value: 'all', label: 'All' },
];

export const DISPATCH_SEVERITY_OPTIONS: FilterOption<DispatchSeverity>[] = [
  { value: 'major', label: 'Major incidents' },
  { value: 'all', label: 'All severities' },
  { value: 'maintenance', label: 'Maintenance only' },
];

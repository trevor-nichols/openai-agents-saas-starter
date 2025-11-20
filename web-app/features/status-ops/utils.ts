import { formatSubscriptionStatus, type StatusSubscriptionStatus } from '@/types/statusSubscriptions';

type InlineTone = 'default' | 'positive' | 'warning';

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

export function resolveStatusTone(status: StatusSubscriptionStatus): InlineTone {
  const normalized = status.toLowerCase();
  if (normalized.includes('active')) return 'positive';
  if (normalized.includes('pending')) return 'warning';
  return 'default';
}

export function formatSeverityLabel(value: string | null | undefined): string {
  if (!value) return 'All';
  const normalized = value.replace(/_/g, ' ').trim();
  return normalized.length > 0
    ? normalized.charAt(0).toUpperCase() + normalized.slice(1)
    : 'All';
}

export function formatStatusLabel(status: StatusSubscriptionStatus): string {
  return formatSubscriptionStatus(status);
}

import type { ComponentProps } from 'react';

import { InlineTag } from '@/components/ui/foundation';
import type { ServiceAccountTokenRow } from '@/types/serviceAccounts';

export type InlineTagTone = ComponentProps<typeof InlineTag>['tone'];

export function resolveTokenStatus(token: ServiceAccountTokenRow): { label: string; tone: InlineTagTone } {
  if (token.revokedAt) {
    return { label: 'Revoked', tone: 'warning' };
  }
  if (isPast(token.expiresAt)) {
    return { label: 'Expired', tone: 'default' };
  }
  return { label: 'Active', tone: 'positive' };
}

export function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }
  return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

export function isPast(value: string): boolean {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return false;
  }
  return date.getTime() < Date.now();
}

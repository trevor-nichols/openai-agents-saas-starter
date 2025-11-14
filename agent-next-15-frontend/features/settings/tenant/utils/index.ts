import type { BillingContact } from '@/types/tenantSettings';

import type { PlanMetadataEntry } from '../types';

function randomId(prefix: string): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

export function createEmptyContact(): BillingContact {
  return {
    id: randomId('contact'),
    name: '',
    email: '',
    role: null,
    phone: null,
    notifyBilling: true,
  };
}

export function recordToEntries(record: Record<string, string>): PlanMetadataEntry[] {
  return Object.entries(record).map(([key, value]) => ({
    id: randomId('meta'),
    key,
    value,
  }));
}

export function entriesToRecord(entries: PlanMetadataEntry[]): Record<string, string> {
  return entries.reduce<Record<string, string>>((acc, entry) => {
    const trimmedKey = entry.key.trim();
    if (!trimmedKey) {
      return acc;
    }
    acc[trimmedKey] = entry.value.trim();
    return acc;
  }, {});
}

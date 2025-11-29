'use client';

import { useSilentRefresh } from '@/lib/queries/session';

export function SilentRefresh() {
  useSilentRefresh();
  return null;
}

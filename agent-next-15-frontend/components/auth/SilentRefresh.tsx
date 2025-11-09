'use client';

import { useSilentRefresh } from '@/hooks/useSilentRefresh';

export function SilentRefresh() {
  useSilentRefresh();
  return null;
}

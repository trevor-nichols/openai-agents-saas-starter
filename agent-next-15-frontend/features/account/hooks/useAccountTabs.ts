'use client';

import { useEffect, useMemo, useState } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

import { ACCOUNT_TABS } from '../constants';
import type { AccountTabKey } from '../types';

function isTabKey(value: string): value is AccountTabKey {
  return ACCOUNT_TABS.some((option) => option.key === value);
}

export function useAccountTabs(initialTab: string = 'profile') {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const sanitizedTab = useMemo(() => (isTabKey(initialTab) ? initialTab : 'profile'), [initialTab]);
  const [tab, setTab] = useState<AccountTabKey>(sanitizedTab);

  useEffect(() => {
    setTab(sanitizedTab);
  }, [sanitizedTab]);

  const handleTabChange = (value: string) => {
    if (!isTabKey(value)) return;
    setTab(value);

    if (typeof window === 'undefined') {
      return;
    }

    const params = new URLSearchParams(searchParams?.toString());
    params.set('tab', value);
    const nextUrl = `${pathname}?${params.toString()}`;
    router.replace(nextUrl, { scroll: false });
  };

  return {
    tab,
    handleTabChange,
  };
}

'use client';

import { useCallback, useEffect, useState } from 'react';

import type { LocationHint } from '@/lib/api/client/types.gen';

const SHARE_LOCATION_KEY = 'chat.shareLocation';
const LOCATION_HINT_KEY = 'chat.locationHint';

function getDefaultLocationHint(): Partial<LocationHint> {
  return { timezone: Intl?.DateTimeFormat?.().resolvedOptions().timeZone };
}

export function useChatWorkspacePreferences() {
  const [shareLocation, setShareLocation] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    try {
      const stored = window.localStorage.getItem(SHARE_LOCATION_KEY);
      if (stored !== null) {
        return stored === 'true';
      }
    } catch {
      // Ignore storage errors.
    }
    return false;
  });

  const [locationHint, setLocationHint] = useState<Partial<LocationHint>>(() => {
    const fallback = getDefaultLocationHint();
    if (typeof window === 'undefined') return fallback;
    try {
      const stored = window.localStorage.getItem(LOCATION_HINT_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as Partial<LocationHint>;
        return { ...fallback, ...parsed };
      }
    } catch {
      // Ignore storage errors.
    }
    return fallback;
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      window.localStorage.setItem(SHARE_LOCATION_KEY, String(shareLocation));
      window.localStorage.setItem(LOCATION_HINT_KEY, JSON.stringify(locationHint));
    } catch {
      // Ignore storage errors.
    }
  }, [shareLocation, locationHint]);

  const updateLocationField = useCallback((field: keyof LocationHint, value: string) => {
    setLocationHint((prev) => ({
      ...prev,
      [field]: value,
    }));
  }, []);

  return {
    shareLocation,
    setShareLocation,
    locationHint,
    updateLocationField,
  };
}

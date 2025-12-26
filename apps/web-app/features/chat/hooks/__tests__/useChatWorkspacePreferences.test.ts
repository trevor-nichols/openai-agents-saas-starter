import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, beforeEach } from 'vitest';

import { useChatWorkspacePreferences } from '../useChatWorkspacePreferences';

const SHARE_KEY = 'chat.shareLocation';
const LOCATION_KEY = 'chat.locationHint';

describe('useChatWorkspacePreferences', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('hydrates from localStorage when values exist', () => {
    window.localStorage.setItem(SHARE_KEY, 'true');
    window.localStorage.setItem(LOCATION_KEY, JSON.stringify({ city: 'Austin' }));

    const { result } = renderHook(() => useChatWorkspacePreferences());

    expect(result.current.shareLocation).toBe(true);
    expect(result.current.locationHint.city).toBe('Austin');
    expect('timezone' in result.current.locationHint).toBe(true);
  });

  it('persists updates to localStorage', async () => {
    const { result } = renderHook(() => useChatWorkspacePreferences());

    await act(async () => {
      result.current.setShareLocation(true);
      result.current.updateLocationField('city', 'Denver');
    });

    expect(window.localStorage.getItem(SHARE_KEY)).toBe('true');
    const stored = window.localStorage.getItem(LOCATION_KEY);
    expect(stored).not.toBeNull();
    expect(JSON.parse(stored ?? '{}').city).toBe('Denver');
  });
});

'use client';

import { useCallback, useState } from 'react';

export type WorkflowPreviewMode = 'graph' | 'outline';

const STORAGE_KEY = 'workflows:previewMode';

function isPreviewMode(value: string | null): value is WorkflowPreviewMode {
  return value === 'graph' || value === 'outline';
}

export function useWorkflowPreviewMode(defaultValue: WorkflowPreviewMode = 'graph') {
  const [mode, setModeState] = useState<WorkflowPreviewMode>(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (isPreviewMode(stored)) return stored;
    } catch {
      // Ignore storage errors (private mode, disabled storage, etc.)
    }
    return defaultValue;
  });

  const setMode = useCallback((next: WorkflowPreviewMode) => {
    setModeState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Ignore storage errors (private mode, disabled storage, etc.)
    }
  }, []);

  return { mode, setMode };
}

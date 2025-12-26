'use client';

import { useMemo, useState } from 'react';

interface VectorStoreRef {
  id: string;
}

export function useVectorStoreSelection(stores: readonly VectorStoreRef[]) {
  const [rawSelectedId, setRawSelectedId] = useState<string | null>(null);

  const selectedId = useMemo(() => {
    if (!rawSelectedId) return null;
    return stores.some((store) => store.id === rawSelectedId) ? rawSelectedId : null;
  }, [rawSelectedId, stores]);

  return {
    selectedId,
    selectVectorStore: setRawSelectedId,
  };
}

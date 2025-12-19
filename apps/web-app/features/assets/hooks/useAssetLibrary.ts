import { useCallback, useMemo, useState } from 'react';

import type { AssetListParams } from '@/lib/api/assets';

export type AssetLibraryTab = 'all' | 'images' | 'files';

export type AssetFilterDraft = {
  conversationId: string;
  agentKey: string;
  sourceTool: AssetListParams['sourceTool'] | '';
  mimeTypePrefix: string;
  createdAfter: string;
  createdBefore: string;
};

const EMPTY_DRAFT: AssetFilterDraft = {
  conversationId: '',
  agentKey: '',
  sourceTool: '',
  mimeTypePrefix: '',
  createdAfter: '',
  createdBefore: '',
};

function toIsoDate(value: string, edge: 'start' | 'end'): string | null {
  if (!value) return null;
  const suffix = edge === 'start' ? 'T00:00:00Z' : 'T23:59:59Z';
  return `${value}${suffix}`;
}

export function useAssetLibraryFilters() {
  const [activeTab, setActiveTab] = useState<AssetLibraryTab>('all');
  const [draft, setDraft] = useState<AssetFilterDraft>(EMPTY_DRAFT);
  const [applied, setApplied] = useState<AssetListParams>({});

  const applyFilters = useCallback(() => {
    setApplied({
      conversationId: draft.conversationId.trim() || null,
      agentKey: draft.agentKey.trim() || null,
      sourceTool: draft.sourceTool || null,
      mimeTypePrefix: draft.mimeTypePrefix.trim() || null,
      createdAfter: toIsoDate(draft.createdAfter, 'start'),
      createdBefore: toIsoDate(draft.createdBefore, 'end'),
    });
  }, [draft]);

  const clearFilters = useCallback(() => {
    setDraft(EMPTY_DRAFT);
    setApplied({});
  }, []);

  const queryFilters = useMemo<AssetListParams>(() => {
    const assetType =
      activeTab === 'images'
        ? 'image'
        : activeTab === 'files'
          ? 'file'
          : null;
    return {
      ...applied,
      assetType,
    };
  }, [activeTab, applied]);

  return {
    activeTab,
    setActiveTab,
    draft,
    setDraft,
    applyFilters,
    clearFilters,
    queryFilters,
  };
}

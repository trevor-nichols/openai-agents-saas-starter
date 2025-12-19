import { act, renderHook } from '@testing-library/react';

import { useAssetLibraryFilters } from '../useAssetLibrary';

describe('useAssetLibraryFilters', () => {
  it('maps tabs to asset types', () => {
    const { result } = renderHook(() => useAssetLibraryFilters());

    expect(result.current.queryFilters.assetType).toBeNull();

    act(() => {
      result.current.setActiveTab('images');
    });
    expect(result.current.queryFilters.assetType).toBe('image');

    act(() => {
      result.current.setActiveTab('files');
    });
    expect(result.current.queryFilters.assetType).toBe('file');
  });

  it('applies date filters as ISO bounds', () => {
    const { result } = renderHook(() => useAssetLibraryFilters());

    act(() => {
      result.current.setDraft({
        ...result.current.draft,
        createdAfter: '2025-01-01',
        createdBefore: '2025-01-02',
      });
    });

    act(() => {
      result.current.applyFilters();
    });

    expect(result.current.queryFilters.createdAfter).toBe('2025-01-01T00:00:00Z');
    expect(result.current.queryFilters.createdBefore).toBe('2025-01-02T23:59:59Z');
  });
});

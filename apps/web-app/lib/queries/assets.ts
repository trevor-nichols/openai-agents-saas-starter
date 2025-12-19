import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  deleteAsset,
  getAssetThumbnailUrls,
  listAssets,
  type AssetListParams,
} from '@/lib/api/assets';

import { queryKeys } from './keys';

const DEFAULT_PAGE_SIZE = 20;

export function useAssetsInfiniteQuery(params?: AssetListParams) {
  const pageSize = params?.limit ?? DEFAULT_PAGE_SIZE;

  return useInfiniteQuery({
    queryKey: queryKeys.assets.list({ ...params, limit: pageSize }),
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      listAssets({
        ...params,
        limit: pageSize,
        offset: pageParam,
      }),
    getNextPageParam: (lastPage) => lastPage.next_offset ?? undefined,
  });
}

export function useDeleteAsset() {
  const client = useQueryClient();

  return useMutation({
    mutationFn: (assetId: string) => deleteAsset(assetId),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: queryKeys.assets.all }).catch(() => {});
    },
  });
}

export function useAssetThumbnailUrls(assetIds: string[]) {
  const normalized = Array.from(new Set(assetIds.filter(Boolean))).sort();

  return useQuery({
    queryKey: queryKeys.assets.thumbnails(normalized),
    queryFn: () => getAssetThumbnailUrls(normalized),
    enabled: normalized.length > 0,
    staleTime: 60_000,
  });
}

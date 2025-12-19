import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { deleteAsset, listAssets, type AssetListParams } from '@/lib/api/assets';

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

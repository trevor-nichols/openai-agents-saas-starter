'use client';

import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { getAssetDownloadUrl } from '@/lib/api/assets';
import {
  useAssetThumbnailUrls,
  useAssetsInfiniteQuery,
  useDeleteAsset,
} from '@/lib/queries/assets';

import { AssetFilters, AssetGallery, AssetTable } from './components';
import { ASSET_LIBRARY_COPY } from './constants';
import { useAssetLibraryFilters } from './hooks/useAssetLibrary';

const PAGE_SIZE = 20;

export function AssetLibrary() {
  const { error: showError } = useToast();
  const deleteAsset = useDeleteAsset();
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { activeTab, setActiveTab, draft, setDraft, applyFilters, clearFilters, queryFilters } =
    useAssetLibraryFilters();

  const assetsQuery = useAssetsInfiniteQuery({ ...queryFilters, limit: PAGE_SIZE });
  const assets = useMemo(
    () => assetsQuery.data?.pages.flatMap((page) => page.items ?? []) ?? [],
    [assetsQuery.data],
  );

  const images = useMemo(() => assets.filter((asset) => asset.asset_type === 'image'), [assets]);
  const files = useMemo(() => assets.filter((asset) => asset.asset_type === 'file'), [assets]);
  const imageIds = useMemo(() => images.map((asset) => asset.id), [images]);
  const thumbnailsQuery = useAssetThumbnailUrls(imageIds);
  const thumbnailUrls = useMemo(() => {
    const items = thumbnailsQuery.data?.items ?? [];
    return items.reduce<Record<string, string>>((acc, item) => {
      acc[item.asset_id] = item.download_url;
      return acc;
    }, {});
  }, [thumbnailsQuery.data]);

  const handleDownload = async (asset: { id: string }) => {
    setDownloadingId(asset.id);
    try {
      const presign = await getAssetDownloadUrl(asset.id);
      window.open(presign.download_url, '_blank', 'noopener,noreferrer');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Download failed';
      showError({ title: 'Could not fetch link', description: message });
    } finally {
      setDownloadingId(null);
    }
  };

  const handleDelete = async (asset: { id: string }) => {
    setDeletingId(asset.id);
    try {
      await deleteAsset.mutateAsync(asset.id);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Delete failed';
      showError({ title: 'Could not delete asset', description: message });
    } finally {
      setDeletingId(null);
    }
  };

  const handlePreview = async (asset: { id: string }) => {
    try {
      const presign = await getAssetDownloadUrl(asset.id);
      return presign.download_url;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Preview failed';
      showError({ title: 'Preview unavailable', description: message });
      return null;
    }
  };

  const hasAssets = assets.length > 0;

  return (
    <section className="space-y-6">
      <SectionHeader
        eyebrow={ASSET_LIBRARY_COPY.eyebrow}
        title={ASSET_LIBRARY_COPY.title}
        description={ASSET_LIBRARY_COPY.description}
        actions={
          <div className="flex items-center gap-3">
            <InlineTag tone={hasAssets ? 'positive' : 'default'}>
              {assetsQuery.isLoading
                ? 'Loading…'
                : assetsQuery.isFetching
                  ? 'Refreshing…'
                  : `${assets.length} assets`}
            </InlineTag>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => assetsQuery.refetch()}
              disabled={assetsQuery.isFetching}
            >
              Refresh
            </Button>
          </div>
        }
      />

      <GlassPanel className="p-4">
        <AssetFilters
          draft={draft}
          onChange={setDraft}
          onApply={applyFilters}
          onClear={clearFilters}
          disabled={assetsQuery.isFetching}
        />
      </GlassPanel>

      {assetsQuery.isLoading ? (
        <GlassPanel className="p-4">
          <SkeletonPanel lines={8} />
        </GlassPanel>
      ) : assetsQuery.isError ? (
        <ErrorState title="Unable to load assets" />
      ) : !hasAssets ? (
        <EmptyState
          title="No assets yet"
          description="Generate images or files in chat to see them here."
        />
      ) : (
        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as typeof activeTab)}>
          <TabsList className="flex flex-wrap gap-2">
            <TabsTrigger value="all">All ({assets.length})</TabsTrigger>
            <TabsTrigger value="images">Images ({images.length})</TabsTrigger>
            <TabsTrigger value="files">Files ({files.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-6">
            <GlassPanel className="p-4">
              <div className="flex items-center justify-between pb-3">
                <h3 className="text-sm font-semibold">Images</h3>
                <InlineTag tone="default">{images.length} loaded</InlineTag>
              </div>
              <AssetGallery
                assets={images}
                thumbnailUrls={thumbnailUrls}
                onDownload={handleDownload}
                onDelete={handleDelete}
                onPreview={handlePreview}
                downloadingId={downloadingId}
                deletingId={deletingId}
              />
            </GlassPanel>

            <GlassPanel className="p-4">
              <div className="flex items-center justify-between pb-3">
                <h3 className="text-sm font-semibold">Files</h3>
                <InlineTag tone="default">{files.length} loaded</InlineTag>
              </div>
              <AssetTable
                assets={files}
                isLoading={assetsQuery.isFetching}
                error={assetsQuery.isError ? 'Unable to load files' : null}
                onDownload={handleDownload}
                onDelete={handleDelete}
                downloadingId={downloadingId}
                deletingId={deletingId}
              />
            </GlassPanel>
          </TabsContent>

          <TabsContent value="images" className="space-y-4">
            <AssetGallery
              assets={images}
              thumbnailUrls={thumbnailUrls}
              onDownload={handleDownload}
              onDelete={handleDelete}
              onPreview={handlePreview}
              downloadingId={downloadingId}
              deletingId={deletingId}
            />
          </TabsContent>

          <TabsContent value="files" className="space-y-4">
            <AssetTable
              assets={files}
              isLoading={assetsQuery.isFetching}
              error={assetsQuery.isError ? 'Unable to load files' : null}
              onDownload={handleDownload}
              onDelete={handleDelete}
              downloadingId={downloadingId}
              deletingId={deletingId}
            />
          </TabsContent>
        </Tabs>
      )}

      {assetsQuery.hasNextPage ? (
        <div className="flex justify-center">
          <Button
            size="sm"
            variant="outline"
            onClick={() => assetsQuery.fetchNextPage()}
            disabled={assetsQuery.isFetchingNextPage}
          >
            {assetsQuery.isFetchingNextPage ? 'Loading…' : 'Load more'}
          </Button>
        </div>
      ) : null}
    </section>
  );
}

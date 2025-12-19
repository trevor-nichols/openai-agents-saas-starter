'use client';

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { InlineTag } from '@/components/ui/foundation';
import { EmptyState } from '@/components/ui/states';

import type { AssetResponse } from '@/lib/api/client/types.gen';
import { formatBytes, formatToolLabel } from '../utils/formatters';
import { DeleteAssetDialog } from './DeleteAssetDialog';

interface AssetGalleryProps {
  assets: AssetResponse[];
  onDownload: (asset: AssetResponse) => Promise<void>;
  onDelete: (asset: AssetResponse) => Promise<void>;
  onPreview: (asset: AssetResponse) => Promise<string | null>;
  downloadingId?: string | null;
  deletingId?: string | null;
}

export function AssetGallery({
  assets,
  onDownload,
  onDelete,
  onPreview,
  downloadingId,
  deletingId,
}: AssetGalleryProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewAsset, setPreviewAsset] = useState<AssetResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  if (!assets.length) {
    return (
      <EmptyState
        title="No images found"
        description="Try adjusting your filters or generate a new image."
      />
    );
  }

  const handlePreview = async (asset: AssetResponse) => {
    setPreviewLoading(true);
    setPreviewAsset(asset);
    try {
      const url = await onPreview(asset);
      setPreviewUrl(url);
    } finally {
      setPreviewLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {assets.map((asset) => {
          const isDownloading = downloadingId === asset.id;
          const isDeleting = deletingId === asset.id;
          return (
            <Card key={asset.id} className="border-white/10 bg-white/5">
              <CardContent className="p-0">
                <div className="relative flex h-40 items-center justify-center overflow-hidden rounded-t-xl bg-gradient-to-br from-slate-900/70 via-slate-800/70 to-slate-700/70 text-xs text-white/70">
                  <div className="absolute inset-0 opacity-30 blur-2xl" />
                  <span className="z-10">Image ready</span>
                </div>
                <div className="space-y-2 px-4 py-3">
                  <div className="text-sm font-semibold text-foreground">
                    {asset.filename ?? `Asset ${asset.id.substring(0, 8)}…`}
                  </div>
                  <div className="text-xs text-foreground/60">
                    {asset.mime_type ?? 'image'} • {formatBytes(asset.size_bytes ?? 0)}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <InlineTag tone="default">{formatToolLabel(asset.source_tool)}</InlineTag>
                    {asset.agent_key ? (
                      <InlineTag tone="default">{asset.agent_key}</InlineTag>
                    ) : null}
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex gap-2 px-4 pb-4">
                <Button size="sm" variant="secondary" onClick={() => handlePreview(asset)}>
                  Preview
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={isDownloading}
                  onClick={() => onDownload(asset)}
                >
                  {isDownloading ? 'Fetching…' : 'Download'}
                </Button>
                <DeleteAssetDialog
                  assetLabel={asset.filename ?? 'this asset'}
                  isPending={isDeleting}
                  onConfirm={() => onDelete(asset)}
                >
                  <Button size="sm" variant="ghost" disabled={isDeleting}>
                    Delete
                  </Button>
                </DeleteAssetDialog>
              </CardFooter>
            </Card>
          );
        })}
      </div>

      <Dialog
        open={Boolean(previewAsset)}
        onOpenChange={(open) => {
          if (!open) {
            setPreviewAsset(null);
            setPreviewUrl(null);
          }
        }}
      >
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>{previewAsset?.filename ?? 'Image preview'}</DialogTitle>
          </DialogHeader>
          <div className="flex min-h-[320px] items-center justify-center rounded-lg border border-white/10 bg-black/60">
            {previewLoading ? (
              <span className="text-sm text-white/70">Loading preview…</span>
            ) : previewUrl ? (
              // eslint-disable-next-line @next/next/no-img-element -- presigned URLs are safe for previews
              <img src={previewUrl} alt={previewAsset?.filename ?? 'preview'} className="max-h-[70vh] w-full object-contain" />
            ) : (
              <span className="text-sm text-white/70">Preview unavailable.</span>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

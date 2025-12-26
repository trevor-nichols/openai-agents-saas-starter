'use client';

import { FileText, Loader2, Plus, RefreshCw, Trash2 } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';
import { useDeleteVectorStoreFile, useVectorStoreFilesQuery } from '@/lib/queries/vectorStores';

import { VectorStoreUploadForm } from './VectorStoreUploadForm';

interface VectorStoreFilesPanelProps {
  vectorStoreId: string;
}

export function VectorStoreFilesPanel({ vectorStoreId }: VectorStoreFilesPanelProps) {
  const [showUpload, setShowUpload] = useState(false);
  const filesQuery = useVectorStoreFilesQuery(vectorStoreId, true);
  const deleteFile = useDeleteVectorStoreFile(vectorStoreId);

  return (
    <div className="flex flex-col h-full rounded-lg border border-border/50 bg-card/30 backdrop-blur-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border/50 bg-muted/20 px-4 py-3">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold">Attached Files</h3>
        </div>
        <div className="flex items-center gap-1">
          <Button
            size="sm"
            variant={showUpload ? 'secondary' : 'outline'}
            className="h-7 text-xs"
            onClick={() => setShowUpload(!showUpload)}
          >
            <Plus className="mr-1 h-3 w-3" />
            Add File
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={() => filesQuery.refetch()}
            disabled={filesQuery.isLoading}
            title="Refresh Files"
          >
            <RefreshCw className={cn("h-3 w-3", filesQuery.isLoading && "animate-spin")} />
          </Button>
        </div>
      </div>

      {/* Upload Form Area */}
      {showUpload && (
        <div className="border-b border-border/50 bg-muted/10 p-4 animate-in slide-in-from-top-2">
          <VectorStoreUploadForm vectorStoreId={vectorStoreId} />
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-auto min-h-[300px]">
        {filesQuery.isLoading ? (
          <div className="p-4">
             <SkeletonPanel lines={4} />
          </div>
        ) : filesQuery.isError ? (
          <div className="p-6">
            <ErrorState title="Failed to load files" />
          </div>
        ) : filesQuery.data?.items.length ? (
           <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent border-border/50">
                <TableHead>Filename</TableHead>
                <TableHead className="w-[100px] text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filesQuery.data.items.map((file) => (
                <TableRow key={file.id} className="border-border/50 hover:bg-muted/30">
                  <TableCell className="py-2">
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-foreground">{file.filename}</span>
                      <span className="text-[10px] font-mono text-muted-foreground">{file.id}</span>
                    </div>
                  </TableCell>
                  <TableCell className="py-2 text-right">
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8 text-muted-foreground hover:text-destructive"
                      onClick={() => deleteFile.mutate(file.id)}
                      disabled={deleteFile.isPending}
                      title="Remove File"
                    >
                      {deleteFile.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <div className="p-8">
             <EmptyState 
              title="No files attached" 
              description="Upload files to this vector store to begin indexing." 
            />
          </div>
        )}
      </div>
    </div>
  );
}

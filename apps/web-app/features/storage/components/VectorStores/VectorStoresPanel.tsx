'use client';

import { Plus, RefreshCw } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { cn } from '@/lib/utils';
import { useDeleteVectorStore, useVectorStoresQuery } from '@/lib/queries/vectorStores';

import { useVectorStoreSelection } from '../../hooks/useVectorStoreSelection';
import { VectorStoreCreateForm } from './VectorStoreCreateForm';
import { VectorStoreFilesPanel } from './VectorStoreFilesPanel';
import { VectorStoreList } from './VectorStoreList';

export function VectorStoresPanel() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const vectorStoresQuery = useVectorStoresQuery();
  const deleteVector = useDeleteVectorStore();
  const stores = vectorStoresQuery.data?.items ?? [];
  const { selectedId, selectVectorStore } = useVectorStoreSelection(stores);

  return (
    <GlassPanel className="p-0 overflow-hidden flex flex-col h-[600px]">
      <div className="flex-1 grid md:grid-cols-[350px_1fr] h-full divide-x divide-border/50">
        
        {/* Left Column: List */}
        <div className="flex flex-col h-full bg-muted/5">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border/50">
            <div>
              <h3 className="text-sm font-semibold">Vector Stores</h3>
              <p className="text-xs text-muted-foreground">Manage your vector indices.</p>
            </div>
            <div className="flex gap-1">
              <Button
                size="icon"
                variant="ghost"
                onClick={() => vectorStoresQuery.refetch()}
                disabled={vectorStoresQuery.isLoading}
                title="Refresh"
                className="h-8 w-8"
              >
                 <RefreshCw className={cn("h-4 w-4", vectorStoresQuery.isLoading && "animate-spin")} />
              </Button>
              
              <Popover open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                <PopoverTrigger asChild>
                  <Button size="icon" variant="secondary" className="h-8 w-8" title="New Store">
                    <Plus className="h-4 w-4" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent align="start" className="w-80 p-4">
                  <div className="space-y-2 mb-4">
                    <h4 className="font-medium leading-none">New Vector Store</h4>
                    <p className="text-xs text-muted-foreground">Create a new container for your embeddings.</p>
                  </div>
                  <VectorStoreCreateForm onSuccess={() => setIsCreateOpen(false)} />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          {/* List Content */}
          <div className="flex-1 overflow-y-auto p-3">
            <VectorStoreList
              items={stores}
              selectedId={selectedId}
              isLoading={vectorStoresQuery.isLoading}
              isError={vectorStoresQuery.isError}
              errorMessage={
                vectorStoresQuery.error instanceof Error
                  ? vectorStoresQuery.error.message
                  : undefined
              }
              isDeleting={deleteVector.isPending}
              onSelect={selectVectorStore}
              onDelete={(id) => deleteVector.mutate(id)}
            />
          </div>
        </div>

        {/* Right Column: Details */}
        <div className="flex flex-col h-full bg-background/30 overflow-hidden">
          {selectedId ? (
            <div className="p-4 h-full overflow-hidden">
               <VectorStoreFilesPanel vectorStoreId={selectedId} />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground p-8 text-center">
              <div className="rounded-full bg-muted/20 p-4 mb-4">
                <Plus className="h-8 w-8 opacity-20" />
              </div>
              <p className="text-sm font-medium">No Vector Store Selected</p>
              <p className="text-xs opacity-60 max-w-[200px] mt-1">
                Select a store from the list to view and manage its files.
              </p>
            </div>
          )}
        </div>
      </div>
    </GlassPanel>
  );
}

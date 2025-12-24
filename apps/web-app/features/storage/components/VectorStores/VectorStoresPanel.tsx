'use client';

import { GlassPanel } from '@/components/ui/foundation';
import { useDeleteVectorStore, useVectorStoresQuery } from '@/lib/queries/vectorStores';

import { useVectorStoreSelection } from '../../hooks/useVectorStoreSelection';
import { VectorStoreCreateForm } from './VectorStoreCreateForm';
import { VectorStoreFilesPanel } from './VectorStoreFilesPanel';
import { VectorStoreHeader } from './VectorStoreHeader';
import { VectorStoreList } from './VectorStoreList';

export function VectorStoresPanel() {
  const vectorStoresQuery = useVectorStoresQuery();
  const deleteVector = useDeleteVectorStore();
  const stores = vectorStoresQuery.data?.items ?? [];
  const { selectedId, selectVectorStore } = useVectorStoreSelection(stores);

  return (
    <GlassPanel className="p-4 space-y-3">
      <VectorStoreHeader
        isRefreshing={vectorStoresQuery.isLoading}
        onRefresh={() => vectorStoresQuery.refetch()}
      />
      <VectorStoreCreateForm />
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

      {selectedId ? <VectorStoreFilesPanel vectorStoreId={selectedId} /> : null}
    </GlassPanel>
  );
}

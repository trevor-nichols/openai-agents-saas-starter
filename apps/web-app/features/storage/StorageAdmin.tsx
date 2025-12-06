'use client';

import { SectionHeader } from '@/components/ui/foundation';

import { StorageObjectsPanel, VectorStoresPanel } from './components';

export function StorageAdmin() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Storage & Vector Assets"
        description="Admin-only surface for object storage and vector stores."
      />

      <StorageObjectsPanel />
      <VectorStoresPanel />
    </div>
  );
}

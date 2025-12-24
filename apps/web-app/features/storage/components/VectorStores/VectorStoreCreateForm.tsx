'use client';

import { useCallback, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { useCreateVectorStore } from '@/lib/queries/vectorStores';

export function VectorStoreCreateForm() {
  const [newVsName, setNewVsName] = useState('');
  const createVector = useCreateVectorStore();
  const { error: showErrorToast } = useToast();

  const handleCreate = useCallback(() => {
    const trimmed = newVsName.trim();
    if (!trimmed) return;
    createVector.mutate(
      { name: trimmed, description: null, metadata: null, expires_after: null },
      {
        onSuccess: () => setNewVsName(''),
        onError: (error) => {
          const message = error instanceof Error ? error.message : 'Unable to create vector store.';
          showErrorToast({ title: 'Vector store create failed', description: message });
        },
      },
    );
  }, [createVector, newVsName, showErrorToast]);

  return (
    <div className="flex gap-2 items-end">
      <div className="space-y-1">
        <Label className="text-xs text-foreground/70">Name</Label>
        <Input
          value={newVsName}
          onChange={(e) => setNewVsName(e.target.value)}
          placeholder="New vector store"
        />
      </div>
      <Button size="sm" onClick={handleCreate} disabled={createVector.isPending}>
        Create
      </Button>
    </div>
  );
}

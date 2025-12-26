'use client';

import { Loader2 } from 'lucide-react';
import { useCallback, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { useCreateVectorStore } from '@/lib/queries/vectorStores';

interface VectorStoreCreateFormProps {
  onSuccess?: () => void;
}

export function VectorStoreCreateForm({ onSuccess }: VectorStoreCreateFormProps) {
  const [newVsName, setNewVsName] = useState('');
  const createVector = useCreateVectorStore();
  const { error: showErrorToast } = useToast();

  const handleCreate = useCallback(() => {
    const trimmed = newVsName.trim();
    if (!trimmed) return;
    
    createVector.mutate(
      { name: trimmed, description: null, metadata: null, expires_after: null },
      {
        onSuccess: () => {
          setNewVsName('');
          onSuccess?.();
        },
        onError: (error) => {
          const message = error instanceof Error ? error.message : 'Unable to create vector store.';
          showErrorToast({ title: 'Vector store create failed', description: message });
        },
      },
    );
  }, [createVector, newVsName, onSuccess, showErrorToast]);

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label className="text-sm font-medium">Name</Label>
        <Input
          value={newVsName}
          onChange={(e) => setNewVsName(e.target.value)}
          placeholder="My Vector Store"
          className="bg-background"
          onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
        />
        <p className="text-[10px] text-muted-foreground">
          Give your vector store a unique name to identify it easily.
        </p>
      </div>
      <Button 
        size="sm" 
        onClick={handleCreate} 
        disabled={createVector.isPending || !newVsName.trim()}
        className="w-full"
      >
        {createVector.isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Creating...
          </>
        ) : (
          'Create Vector Store'
        )}
      </Button>
    </div>
  );
}

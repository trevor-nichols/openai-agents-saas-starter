import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { SkeletonPanel, EmptyState, ErrorState } from '@/components/ui/states';
import type { ContainerResponse } from '@/lib/api/client/types.gen';

interface ContainerBindingsPanelProps {
  containers: ContainerResponse[];
  isLoading: boolean;
  error?: Error | null;
  selectedContainerId: string | null;
  onSelect: (id: string) => void;
  onCreate: (name: string, memoryLimit?: string | null) => void;
  onDelete: (id: string) => void;
  onBind: (containerId: string) => void;
  onUnbind: () => void;
  agentKey: string;
}

export function ContainerBindingsPanel({
  containers,
  isLoading,
  error,
  selectedContainerId,
  onSelect,
  onCreate,
  onDelete,
  onBind,
  onUnbind,
  agentKey,
}: ContainerBindingsPanelProps) {
  const [name, setName] = useState('');
  const [memoryLimit, setMemoryLimit] = useState<string | undefined>(undefined);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold">Containers</div>
          <p className="text-xs text-foreground/60">Bind the selected agent to a container.</p>
        </div>
      </div>

      <div className="flex gap-2 items-end">
        <div className="space-y-1">
          <Label className="text-xs">Name</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Container name" className="max-w-xs" />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Memory (e.g., 4g)</Label>
          <Input value={memoryLimit ?? ''} onChange={(e) => setMemoryLimit(e.target.value || undefined)} placeholder="4g" className="max-w-[120px]" />
        </div>
        <Button size="sm" onClick={() => name.trim() && onCreate(name.trim(), memoryLimit ?? null)} disabled={isLoading}>
          Create
        </Button>
      </div>

      {isLoading ? (
        <SkeletonPanel lines={6} />
      ) : error ? (
        <ErrorState title="Failed to load containers" message={error.message} />
      ) : containers.length === 0 ? (
        <EmptyState title="No containers" description="Create a container to bind agents." />
      ) : (
        <div className="space-y-2">
          {containers.map((ctr) => (
            <div key={ctr.id} className="flex items-center justify-between rounded-lg border border-white/5 bg-white/5 px-3 py-2 text-sm">
              <div className="space-y-1">
                <div className="font-semibold">{ctr.name}</div>
                <div className="text-xs text-foreground/60">Memory: {ctr.memory_limit}</div>
                <div className="text-[11px] text-foreground/50">Status: {ctr.status}</div>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant={selectedContainerId === ctr.id ? 'default' : 'secondary'}
                  onClick={() => onSelect(ctr.id)}
                >
                  {selectedContainerId === ctr.id ? 'Selected' : 'Select'}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => onDelete(ctr.id)}>
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <Button
          size="sm"
          onClick={() => selectedContainerId && onBind(selectedContainerId)}
          disabled={!selectedContainerId || isLoading}
        >
          Bind agent {agentKey}
        </Button>
        <Button size="sm" variant="ghost" onClick={onUnbind} disabled={isLoading}>
          Unbind
        </Button>
      </div>
    </div>
  );
}

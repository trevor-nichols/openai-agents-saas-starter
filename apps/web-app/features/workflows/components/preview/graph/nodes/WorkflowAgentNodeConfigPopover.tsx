'use client';

import { useMemo } from 'react';
import { Settings2 } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { InlineTag } from '@/components/ui/foundation';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectItemDescription,
  SelectItemTitle,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { ContainerResponse, VectorStoreResponse } from '@/lib/api/client/types.gen';

type OverrideItem = {
  id: string;
  title: string;
  description: string;
};

type ResourceOverrideSectionProps = {
  title: string;
  tagLabel: string;
  loadingLabel: string;
  emptyLabel: string;
  autoTitle: string;
  autoDescription: string;
  items: OverrideItem[];
  value: string | null;
  error: string | null;
  isLoading: boolean;
  onChange?: (value: string | null) => void;
  footer?: string;
};

function ResourceOverrideSection({
  title,
  tagLabel,
  loadingLabel,
  emptyLabel,
  autoTitle,
  autoDescription,
  items,
  value,
  error,
  isLoading,
  onChange,
  footer,
}: ResourceOverrideSectionProps) {
  const resolvedValue = value ?? 'auto';
  const handleChange = onChange
    ? (nextValue: string) => {
        onChange(nextValue === 'auto' ? null : nextValue);
      }
    : undefined;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-wide text-muted-foreground">{title}</p>
        <InlineTag tone="default">{tagLabel}</InlineTag>
      </div>
      {error ? (
        <p className="text-xs text-destructive">{error}</p>
      ) : isLoading ? (
        <p className="text-xs text-muted-foreground">{loadingLabel}</p>
      ) : items.length === 0 ? (
        <p className="text-xs text-muted-foreground">{emptyLabel}</p>
      ) : (
        <Select value={resolvedValue} onValueChange={handleChange}>
          <SelectTrigger>
            <SelectValue placeholder={autoTitle} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="auto">
              <SelectItemTitle>{autoTitle}</SelectItemTitle>
              <SelectItemDescription>{autoDescription}</SelectItemDescription>
            </SelectItem>
            {items.map((item) => (
              <SelectItem key={item.id} value={item.id}>
                <SelectItemTitle>{item.title}</SelectItemTitle>
                <SelectItemDescription>{item.description}</SelectItemDescription>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
      {footer ? <p className="text-[11px] text-muted-foreground">{footer}</p> : null}
    </div>
  );
}

export type WorkflowAgentNodeConfigPopoverProps = {
  agentKey: string;
  tools: string[];
  supportsContainers: boolean;
  supportsFileSearch: boolean;
  containers: ContainerResponse[];
  containersError: string | null;
  isLoadingContainers: boolean;
  selectedContainerId: string | null;
  onContainerOverrideChange?: (agentKey: string, containerId: string | null) => void;
  vectorStores: VectorStoreResponse[];
  vectorStoresError: string | null;
  isLoadingVectorStores: boolean;
  selectedVectorStoreId: string | null;
  onVectorStoreOverrideChange?: (agentKey: string, vectorStoreId: string | null) => void;
};

export function WorkflowAgentNodeConfigPopover({
  agentKey,
  tools,
  supportsContainers,
  supportsFileSearch,
  containers,
  containersError,
  isLoadingContainers,
  selectedContainerId,
  onContainerOverrideChange,
  vectorStores,
  vectorStoresError,
  isLoadingVectorStores,
  selectedVectorStoreId,
  onVectorStoreOverrideChange,
}: WorkflowAgentNodeConfigPopoverProps) {
  const sortedTools = useMemo(() => [...tools].sort((a, b) => a.localeCompare(b)), [tools]);

  const containerItems = useMemo<OverrideItem[]>(
    () =>
      containers.map((container) => ({
        id: container.id,
        title: container.name,
        description: `${container.memory_limit} · ${container.status}`,
      })),
    [containers],
  );

  const vectorStoreItems = useMemo<OverrideItem[]>(
    () =>
      vectorStores.map((store) => ({
        id: store.id,
        title: store.name,
        description: `${store.status} · ${store.usage_bytes ?? 0} bytes`,
      })),
    [vectorStores],
  );

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-muted-foreground hover:text-foreground"
          aria-label={`Configure ${agentKey}`}
        >
          <Settings2 className="h-3.5 w-3.5" />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80 space-y-4">
        <div className="space-y-1">
          <p className="text-sm font-semibold text-foreground">Agent tools</p>
          <p className="text-xs text-muted-foreground">Available capabilities for {agentKey}.</p>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Tools</p>
            <InlineTag tone="default">{sortedTools.length}</InlineTag>
          </div>
          {sortedTools.length ? (
            <ScrollArea className="max-h-32 pr-2">
              <div className="flex flex-wrap gap-2">
                {sortedTools.map((tool) => (
                  <Badge key={`${agentKey}-${tool}`} variant="outline" className="text-[11px]">
                    {tool}
                  </Badge>
                ))}
              </div>
            </ScrollArea>
          ) : (
            <p className="text-xs text-muted-foreground">No tools assigned.</p>
          )}
        </div>

        {supportsContainers ? (
          <ResourceOverrideSection
            title="Container"
            tagLabel="Code Interpreter"
            loadingLabel="Loading containers…"
            emptyLabel="No containers available."
            autoTitle="Auto (managed)"
            autoDescription="Use the default container policy."
            items={containerItems}
            value={selectedContainerId}
            error={containersError}
            isLoading={isLoadingContainers}
            onChange={(containerId) => onContainerOverrideChange?.(agentKey, containerId)}
            footer="Applies to the next workflow run."
          />
        ) : null}

        {supportsFileSearch ? (
          <ResourceOverrideSection
            title="Vector store"
            tagLabel="File Search"
            loadingLabel="Loading vector stores…"
            emptyLabel="No vector stores available."
            autoTitle="Auto (managed)"
            autoDescription="Use the default vector store policy."
            items={vectorStoreItems}
            value={selectedVectorStoreId}
            error={vectorStoresError}
            isLoading={isLoadingVectorStores}
            onChange={(vectorStoreId) => onVectorStoreOverrideChange?.(agentKey, vectorStoreId)}
            footer="Applies to the next workflow run."
          />
        ) : null}
      </PopoverContent>
    </Popover>
  );
}

// File Path: features/chat/components/ToolMetadataPanel.tsx
// Description: Tool registry overview panel for the chat workspace.

'use client';

import { useMemo } from 'react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { GlassPanel, InlineTag } from '@/components/ui/foundation';
import { EmptyState, SkeletonPanel } from '@/components/ui/states';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import type { ToolRegistry } from '@/types/tools';
import { normalizeAgentLabel } from '../utils/formatters';

interface ToolMetadataPanelProps {
  selectedAgentKey: string;
  selectedAgentLabel?: string;
  tools: ToolRegistry;
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void | Promise<void>;
  className?: string;
}

export function ToolMetadataPanel({
  selectedAgentKey,
  selectedAgentLabel,
  tools,
  isLoading,
  error,
  onRefresh,
  className,
}: ToolMetadataPanelProps) {
  const { totalTools, categories, toolNames, perAgent } = useMemo(() => {
    const registry = tools as Record<string, unknown>;
    const categoryList = Array.isArray(registry.categories) ? (registry.categories as string[]) : [];
    const toolNameList = Array.isArray(registry.tool_names) ? (registry.tool_names as string[]) : [];
    const total = Number(registry.total_tools ?? toolNameList.length) || toolNameList.length;
    const perAgentMap = registry.per_agent && typeof registry.per_agent === 'object'
      ? (registry.per_agent as Record<string, unknown>)
      : null;

    return {
      totalTools: total,
      categories: categoryList,
      toolNames: toolNameList,
      perAgent: perAgentMap,
    };
  }, [tools]);

  const resolvedAgentLabel = useMemo(
    () => selectedAgentLabel ?? normalizeAgentLabel(selectedAgentKey),
    [selectedAgentKey, selectedAgentLabel],
  );

  const { list: agentTools, isFallback: isRegistryFallback } = useMemo(() => {
    if (!selectedAgentKey) {
      return { list: toolNames, isFallback: true };
    }

    const entry = perAgent?.[selectedAgentKey];
    if (Array.isArray(entry)) {
      return {
        list: entry.filter((tool): tool is string => typeof tool === 'string'),
        isFallback: false,
      };
    }
    if (typeof entry === 'string') {
      return { list: [entry], isFallback: false };
    }
    if (entry && typeof entry === 'object') {
      const nested = (entry as Record<string, unknown>).tool_names;
      if (Array.isArray(nested)) {
        return {
          list: nested.filter((tool): tool is string => typeof tool === 'string'),
          isFallback: false,
        };
      }
    }
    if (perAgent && Object.prototype.hasOwnProperty.call(perAgent, selectedAgentKey)) {
      return { list: [], isFallback: false };
    }
    return { list: toolNames, isFallback: true };
  }, [perAgent, selectedAgentKey, toolNames]);

  const sortedToolNames = useMemo(
    () => [...agentTools].sort((a, b) => a.localeCompare(b)),
    [agentTools],
  );

  return (
    <GlassPanel className={cn('flex h-full flex-col gap-4', className)}>
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/50">Tools</p>
            <p className="text-sm text-foreground/70">Registry snapshot per agent policy.</p>
          </div>
          {error ? (
            <Button variant="ghost" size="sm" onClick={onRefresh}>
              Retry
            </Button>
          ) : (
            <InlineTag tone="default">{resolvedAgentLabel}</InlineTag>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <InlineTag tone="positive">{totalTools} tools</InlineTag>
          <InlineTag tone="default">{categories.length} categories</InlineTag>
          {isRegistryFallback ? (
            <InlineTag tone="default">Registry default</InlineTag>
          ) : null}
          <Badge variant="outline">Last refreshed just now</Badge>
        </div>
      </div>

      {isLoading ? (
        <SkeletonPanel lines={6} />
      ) : error ? (
        <EmptyState
          title="Tool metadata unavailable"
          description={error}
          action={
            <Button onClick={onRefresh} variant="outline">
              Try again
            </Button>
          }
        />
      ) : (
        <div className="flex flex-1 flex-col gap-4">
          <div className="grid grid-cols-2 gap-4 text-sm text-foreground/60">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/40">Total tools</p>
              <p className="text-2xl font-semibold text-foreground">{totalTools}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/40">Categories</p>
              <p className="text-2xl font-semibold text-foreground">{categories.length}</p>
            </div>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/40">Category tags</p>
            {categories.length === 0 ? (
              <p className="mt-2 text-sm text-foreground/60">No categories reported.</p>
            ) : (
              <div className="mt-2 flex flex-wrap gap-2">
                {categories.map((category) => (
                  <Badge key={category} variant="secondary" className="capitalize">
                    {category.replace('_', ' ')}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          <div className="flex-1">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/40">
                Tools for {resolvedAgentLabel}
              </p>
              <Button variant="ghost" size="sm" onClick={onRefresh}>
                Refresh
              </Button>
            </div>
            {agentTools.length === 0 ? (
              <p className="mt-2 text-sm text-foreground/60">No tools assigned to this agent.</p>
            ) : (
              <ScrollArea className="mt-2 max-h-72 pr-2">
                <ul className="space-y-2 text-sm text-foreground/80">
                  {sortedToolNames.map((tool) => (
                    <li
                      key={tool}
                      className="flex items-center justify-between rounded-xl border border-white/5 bg-white/5 px-3 py-2"
                    >
                      <span>{tool}</span>
                      <Badge variant="outline">agent</Badge>
                    </li>
                  ))}
                </ul>
              </ScrollArea>
            )}
          </div>
        </div>
      )}
    </GlassPanel>
  );
}

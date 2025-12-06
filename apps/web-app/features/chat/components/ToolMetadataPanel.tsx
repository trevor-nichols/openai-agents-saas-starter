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

interface ToolMetadataPanelProps {
  selectedAgent: string;
  tools: ToolRegistry;
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void | Promise<void>;
  className?: string;
}

export function ToolMetadataPanel({
  selectedAgent,
  tools,
  isLoading,
  error,
  onRefresh,
  className,
}: ToolMetadataPanelProps) {
  const { totalTools, categories, toolNames } = useMemo(() => {
    const registry = tools as Record<string, unknown>;
    const categoryList = Array.isArray(registry.categories) ? (registry.categories as string[]) : [];
    const toolNameList = Array.isArray(registry.tool_names) ? (registry.tool_names as string[]) : [];
    const total = Number(registry.total_tools ?? toolNameList.length) || toolNameList.length;

    return {
      totalTools: total,
      categories: categoryList,
      toolNames: toolNameList,
    };
  }, [tools]);

  const sortedToolNames = useMemo(() => [...toolNames].sort((a, b) => a.localeCompare(b)), [toolNames]);

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
            <InlineTag tone="default">{selectedAgent}</InlineTag>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <InlineTag tone="positive">{totalTools} tools</InlineTag>
          <InlineTag tone="default">{categories.length} categories</InlineTag>
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
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/40">Tools available</p>
              <Button variant="ghost" size="sm" onClick={onRefresh}>
                Refresh
              </Button>
            </div>
            {toolNames.length === 0 ? (
              <p className="mt-2 text-sm text-foreground/60">Tool registry returned no entries.</p>
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

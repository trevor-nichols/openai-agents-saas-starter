// File Path: features/chat/components/ToolMetadataPanel.tsx
// Description: Tool registry overview panel for the chat workspace.

'use client';

import { useMemo } from 'react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
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

  return (
    <GlassPanel className={cn("flex h-full flex-col gap-4", className)}>
      <SectionHeader
        eyebrow="Tools"
        title="Agent capabilities"
        description="Registry snapshot scoped by policy."
        actions={
          error ? (
            <Button variant="ghost" size="sm" onClick={onRefresh}>
              Retry
            </Button>
          ) : (
            <InlineTag tone="default">{selectedAgent}</InlineTag>
          )
        }
      />

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
          <dl className="grid grid-cols-2 gap-4 text-sm text-foreground/60">
            <div>
              <dt className="uppercase tracking-[0.3em] text-xs text-foreground/40">Total tools</dt>
              <dd className="text-2xl font-semibold text-foreground">{totalTools}</dd>
            </div>
            <div>
              <dt className="uppercase tracking-[0.3em] text-xs text-foreground/40">Categories</dt>
              <dd className="text-2xl font-semibold text-foreground">{categories.length}</dd>
            </div>
          </dl>

          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/40">Categories</p>
            {categories.length === 0 ? (
              <p className="mt-2 text-sm text-foreground/60">No categories reported.</p>
            ) : (
              <div className="mt-2 flex flex-wrap gap-2">
                {categories.map((category) => (
                  <Badge key={category} variant="secondary" className="capitalize">
                    {category.replace("_", " ")}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          <div className="flex-1">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/40">Tools available</p>
            {toolNames.length === 0 ? (
              <p className="mt-2 text-sm text-foreground/60">Tool registry returned no entries.</p>
            ) : (
              <ScrollArea className="mt-2 max-h-72 pr-2">
                <ul className="space-y-2 text-sm text-foreground/80">
                  {toolNames.map((tool) => (
                    <li key={tool} className="rounded-md border border-white/5 bg-white/5 px-3 py-2">
                      {tool}
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

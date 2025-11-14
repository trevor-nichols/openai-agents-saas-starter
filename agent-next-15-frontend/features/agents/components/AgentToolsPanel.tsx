// File Path: features/agents/components/AgentToolsPanel.tsx
// Description: Insights panel summarizing tool registry health + agent compatibility.

'use client';

import { useMemo } from 'react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { EmptyState, SkeletonPanel } from '@/components/ui/states';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

import type { ToolRegistrySummary, ToolsByAgentMap } from '../types';

interface AgentToolsPanelProps {
  summary: ToolRegistrySummary;
  toolsByAgent: ToolsByAgentMap;
  selectedAgent: string | null;
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void | Promise<void>;
}

export function AgentToolsPanel({
  summary,
  toolsByAgent,
  selectedAgent,
  isLoading,
  error,
  onRefresh,
}: AgentToolsPanelProps) {
  const agentKey = selectedAgent ?? Object.keys(toolsByAgent)[0] ?? null;
  const agentTools = agentKey ? toolsByAgent[agentKey] ?? [] : [];

  const categoriesDisplay = useMemo(() => {
    return summary.categories.map((category) => category.replaceAll('_', ' '));
  }, [summary.categories]);

  if (isLoading) {
    return <SkeletonPanel lines={6} />;
  }

  if (error) {
    return (
      <EmptyState
        title="Tool metadata unavailable"
        description={error}
        action={
          <Button
            onClick={() => {
              void onRefresh();
            }}
          >
            Try again
          </Button>
        }
      />
    );
  }

  return (
    <GlassPanel className="space-y-4">
      <SectionHeader
        eyebrow="Tooling"
        title="Registry coverage"
        description="Snapshot of available tools and how they map to each agent."
        actions={
          <InlineTag tone="default">
            {summary.totalTools ? `${summary.totalTools} registered` : 'No tools'}
          </InlineTag>
        }
      />

      <div className="grid grid-cols-2 gap-4 text-sm text-foreground/60">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/40">Categories</p>
          <p className="text-2xl font-semibold text-foreground">{summary.categories.length}</p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/40">Default agent</p>
          <p className="text-2xl font-semibold text-foreground">{agentKey ?? '—'}</p>
        </div>
      </div>

      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/40">Category tags</p>
        {categoriesDisplay.length === 0 ? (
          <p className="mt-2 text-sm text-foreground/60">No categories reported.</p>
        ) : (
          <div className="mt-2 flex flex-wrap gap-2">
            {categoriesDisplay.map((category) => (
              <Badge key={category} variant="secondary" className="capitalize">
                {category}
              </Badge>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/40">
            {agentKey ? `${agentKey} tools` : 'Agent tools'}
          </p>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              void onRefresh();
            }}
          >
            Refresh
          </Button>
        </div>
        {agentTools.length === 0 ? (
          <EmptyState
            title="No tools assigned"
            description="Assign registry resources to this agent to surface them here."
          />
        ) : (
          <ScrollArea className="max-h-72 pr-3">
            <ul className="space-y-2">
              {agentTools.map((tool) => (
                <li
                  key={`${agentKey}-${tool}`}
                  className={cn(
                    'flex items-center justify-between rounded-xl border border-white/5 bg-white/5 px-3 py-2 text-sm',
                    agentKey === selectedAgent ? 'border-white/30' : undefined,
                  )}
                >
                  <span>{tool}</span>
                  <Badge variant="outline">{agentKey}</Badge>
                </li>
              ))}
            </ul>
          </ScrollArea>
        )}
      </div>
    </GlassPanel>
  );
}

// File Path: features/agents/components/AgentCatalogGrid.tsx
// Description: Presentational grid showing agent health + tooling context.

'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import { ArrowUpRight } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { formatRelativeTime } from '@/lib/utils/time';
import type { AgentSummary } from '@/types/agents';

import type { ToolRegistrySummary, ToolsByAgentMap } from '../types';

interface AgentCatalogGridProps {
  agents: AgentSummary[];
  toolsByAgent: ToolsByAgentMap;
  summary: ToolRegistrySummary;
  isLoadingAgents: boolean;
  isLoadingTools: boolean;
  errorMessage: string | null;
  onRefreshTools: () => void | Promise<void>;
  selectedAgent: string | null;
  onSelectAgent: (agentName: string) => void;
}

export function AgentCatalogGrid({
  agents,
  toolsByAgent,
  summary,
  isLoadingAgents,
  isLoadingTools,
  errorMessage,
  onRefreshTools,
  selectedAgent,
  onSelectAgent,
}: AgentCatalogGridProps) {
  const totalAgents = agents.length;

  const toolingSummary = useMemo(() => {
    if (!summary.totalTools) {
      return 'No shared tools registered';
    }
    return `${summary.totalTools} tool${summary.totalTools === 1 ? '' : 's'} available`;
  }, [summary.totalTools]);

  const isLoading = isLoadingAgents || isLoadingTools;

  if (isLoading) {
    return <SkeletonPanel lines={8} />;
  }

  if (errorMessage) {
    return (
      <ErrorState
        title="Unable to load agent catalog"
        message={errorMessage}
        onRetry={() => {
          void onRefreshTools();
        }}
      />
    );
  }

  if (totalAgents === 0) {
    return (
      <EmptyState
        title="No agents registered yet"
        description="Provision your first agent via the CLI or API, then refresh this page to see live telemetry."
        action={<Button disabled>Create agent</Button>}
      />
    );
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Automation"
        title="Agent catalog"
        description="Inspect active agents, review their telemetry, and route chats with confidence."
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <InlineTag tone={totalAgents ? 'positive' : 'default'}>
              {`${totalAgents} agent${totalAgents === 1 ? '' : 's'}`}
            </InlineTag>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                void onRefreshTools();
              }}
              disabled={isLoadingTools}
            >
              Refresh tools
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link href="/chat">Open workspace</Link>
            </Button>
            <Button size="sm" disabled>
              Create agent
            </Button>
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
        {agents.map((agent) => {
          const agentTools = toolsByAgent[agent.name] ?? [];
          const isSelected = selectedAgent === agent.name;
          return (
            <GlassPanel
              key={agent.name}
              className="flex h-full cursor-pointer flex-col justify-between gap-4 border border-transparent transition hover:border-white/20"
              onClick={() => onSelectAgent(agent.name)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  onSelectAgent(agent.name);
                }
              }}
              role="button"
              tabIndex={0}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-lg font-semibold text-foreground">
                      {agent.display_name ?? agent.name}
                    </p>
                    <p className="text-xs uppercase tracking-[0.2em] text-foreground/60">
                      {agent.model ?? 'Unknown model'}
                    </p>
                  </div>
                  <StatusBadge status={agent.status} />
                </div>
                <p className="text-sm text-foreground/70">
                  {agent.description ?? 'No description provided.'}
                </p>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-foreground/60">
                  <span>Last heartbeat</span>
                  <span>{agent.last_seen_at ? formatRelativeTime(agent.last_seen_at) : '—'}</span>
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-foreground/60">Tools</p>
                  {agentTools.length ? (
                    <div className="flex flex-wrap gap-2">
                      {agentTools.slice(0, 6).map((tool) => (
                        <Badge
                          key={`${agent.name}-${tool}`}
                          variant={isSelected ? 'default' : 'outline'}
                          className="text-xs"
                        >
                          {tool}
                        </Badge>
                      ))}
                      {agentTools.length > 6 ? (
                        <Badge variant="outline" className="text-xs">
                          +{agentTools.length - 6}
                        </Badge>
                      ) : null}
                    </div>
                  ) : (
                    <p className="text-sm text-foreground/50">No tools assigned</p>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-white/10 pt-4 text-sm">
                <span className="text-foreground/60">{toolingSummary}</span>
                <Button
                  variant={isSelected ? 'default' : 'ghost'}
                  size="sm"
                  className="gap-2"
                  aria-pressed={isSelected}
                  onClick={(event) => {
                    event.stopPropagation();
                    onSelectAgent(agent.name);
                  }}
                >
                  {isSelected ? 'Active agent' : 'Route chat'}
                  <ArrowUpRight className="h-4 w-4" />
                </Button>
              </div>
            </GlassPanel>
          );
        })}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status?: string | null }) {
  const normalized = (status ?? 'unknown').toLowerCase();
  if (normalized === 'active') {
    return <Badge className="bg-emerald-500/20 text-emerald-100">Active</Badge>;
  }
  if (normalized === 'paused') {
    return <Badge className="bg-amber-500/20 text-amber-100">Paused</Badge>;
  }
  if (normalized === 'error') {
    return <Badge variant="destructive">Error</Badge>;
  }
  return <Badge variant="outline">Unknown</Badge>;
}

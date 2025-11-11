// File Path: features/agents/AgentsOverview.tsx
// Description: Agent roster view showing model telemetry + tool availability.

'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import { ArrowUpRight } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { useAgents } from '@/lib/queries/agents';
import { useTools } from '@/lib/queries/tools';
import { formatRelativeTime } from '@/lib/utils/time';

export function AgentsOverview() {
  const { agents, isLoadingAgents, agentsError } = useAgents();
  const { tools, isLoading: isLoadingTools, error: toolsError, refetch } = useTools();

  const totalAgents = agents.length;

  const toolingSummary = useMemo(() => {
    if (!tools || Object.keys(tools).length === 0) {
      return 'No shared tools registered';
    }
    const totalTools = Object.keys(tools).length;
    return `${totalTools} tool${totalTools === 1 ? '' : 's'} available`;
  }, [tools]);

  const isLoading = isLoadingAgents || isLoadingTools;
  const combinedError = agentsError?.message ?? toolsError;

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow="Automation"
        title="Agent catalog"
        description="Inspect agent health, understand their capabilities, and preview available tools before routing workloads."
        actions={
          <div className="flex items-center gap-3">
            <InlineTag tone={totalAgents ? 'positive' : 'default'}>
              {isLoading ? 'Loading…' : `${totalAgents} agent${totalAgents === 1 ? '' : 's'}`}
            </InlineTag>
            <Button variant="ghost" size="sm" onClick={() => refetch()} disabled={isLoadingTools}>
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

      {isLoading ? (
        <SkeletonPanel lines={8} />
      ) : combinedError ? (
        <ErrorState
          title="Unable to load agent catalog"
          message={combinedError}
          onRetry={() => {
            void refetch();
          }}
        />
      ) : totalAgents === 0 ? (
        <EmptyState
          title="No agents registered yet"
          description="Provision your first agent via the CLI or API, then refresh this page to see live telemetry."
          action={<Button disabled>Create agent</Button>}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {agents.map((agent) => {
            const agentTools = tools?.[agent.name] ?? [];
            return (
              <GlassPanel key={agent.name} className="flex h-full flex-col justify-between gap-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-lg font-semibold text-foreground">{agent.display_name ?? agent.name}</p>
                      <p className="text-xs uppercase tracking-[0.2em] text-foreground/60">{agent.model ?? 'Unknown model'}</p>
                    </div>
                    <StatusBadge status={agent.status} />
                  </div>
                  <p className="text-sm text-foreground/70">{agent.description ?? 'No description provided.'}</p>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between text-xs text-foreground/60">
                    <span>Last heartbeat</span>
                    <span>{agent.last_seen_at ? formatRelativeTime(agent.last_seen_at) : '—'}</span>
                  </div>
                  <div className="space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-foreground/60">Tools</p>
                    {Array.isArray(agentTools) && agentTools.length ? (
                      <div className="flex flex-wrap gap-2">
                        {agentTools.map((tool) => (
                          <Badge key={`${agent.name}-${tool}`} variant="outline" className="text-xs">
                            {tool}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-foreground/50">No tools assigned</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between border-t border-white/10 pt-4 text-sm">
                  <span className="text-foreground/60">{toolingSummary}</span>
                  <Button variant="ghost" size="sm" className="gap-2" disabled>
                    View details
                    <ArrowUpRight className="h-4 w-4" />
                  </Button>
                </div>
              </GlassPanel>
            );
          })}
        </div>
      )}
    </section>
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

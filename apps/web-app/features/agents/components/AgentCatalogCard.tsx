import { ArrowUpRight } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { GlassPanel } from '@/components/ui/foundation';
import { Button } from '@/components/ui/button';
import { formatRelativeTime } from '@/lib/utils/time';
import type { AgentSummary } from '@/types/agents';

interface AgentCatalogCardProps {
  agent: AgentSummary;
  tools: string[];
  isSelected: boolean;
  onSelect: (agentName: string) => void;
}

export function AgentCatalogCard({ agent, tools, isSelected, onSelect }: AgentCatalogCardProps) {
  const displayName = agent.display_name ?? agent.name;

  return (
    <GlassPanel
      key={agent.name}
      className="flex h-full cursor-pointer flex-col justify-between gap-4 border border-transparent transition hover:border-white/20"
      onClick={() => onSelect(agent.name)}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onSelect(agent.name);
        }
      }}
      role="button"
      tabIndex={0}
    >
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-lg font-semibold text-foreground">{displayName}</p>
            <p className="text-xs uppercase tracking-[0.2em] text-foreground/60">{agent.model ?? 'Unknown model'}</p>
          </div>
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
          {tools.length ? (
            <div className="flex flex-wrap gap-2">
              {tools.slice(0, 6).map((tool) => (
                <Badge key={`${agent.name}-${tool}`} variant={isSelected ? 'default' : 'outline'} className="text-xs">
                  {tool}
                </Badge>
              ))}
              {tools.length > 6 ? (
                <Badge variant="outline" className="text-xs">
                  +{tools.length - 6}
                </Badge>
              ) : null}
            </div>
          ) : (
            <p className="text-sm text-foreground/50">No tools assigned</p>
          )}
        </div>
      </div>

      <div className="flex items-center justify-end border-t border-white/10 pt-4 text-sm">
        <Button
          variant={isSelected ? 'default' : 'ghost'}
          size="sm"
          className="gap-2"
          aria-pressed={isSelected}
          onClick={(event) => {
            event.stopPropagation();
            onSelect(agent.name);
          }}
        >
          {isSelected ? 'Active agent' : 'Route chat'}
          <ArrowUpRight className="h-4 w-4" />
        </Button>
      </div>
    </GlassPanel>
  );
}

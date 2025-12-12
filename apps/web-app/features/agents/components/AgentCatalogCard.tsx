import { ArrowUpRight, Cpu, Wrench } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { formatRelativeTime } from '@/lib/utils/time';
import type { AgentSummary } from '@/types/agents';
import { cn } from '@/lib/utils';

interface AgentCatalogCardProps {
  agent: AgentSummary;
  tools: string[];
  isSelected: boolean;
  onSelect: (agentName: string) => void;
}

export function AgentCatalogCard({ agent, tools, isSelected, onSelect }: AgentCatalogCardProps) {
  const displayName = agent.display_name ?? agent.name;

  return (
    <Card
      key={agent.name}
      className={cn(
        "group flex h-full cursor-pointer flex-col justify-between transition-all duration-200 hover:shadow-md",
        isSelected ? "border-primary/50 bg-primary/5 ring-1 ring-primary/20" : "hover:border-primary/20 hover:bg-muted/30"
      )}
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
      <CardHeader className="space-y-2 p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <CardTitle className="text-base font-semibold leading-tight text-foreground group-hover:text-primary transition-colors">
              {displayName}
            </CardTitle>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Cpu className="h-3 w-3" />
              <span className="uppercase tracking-wider">{agent.model ?? 'Unknown model'}</span>
            </div>
          </div>
          {agent.last_seen_at && (
            <Badge variant="secondary" className="shrink-0 text-[10px] font-normal opacity-70">
              {formatRelativeTime(agent.last_seen_at)}
            </Badge>
          )}
        </div>
        <p className="line-clamp-2 text-sm text-muted-foreground/80">
          {agent.description ?? 'No description provided.'}
        </p>
      </CardHeader>

      <CardContent className="px-5 pb-4 pt-0">
        <div className="space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <Wrench className="h-3 w-3" />
            <span>Tools available</span>
          </div>
          {tools.length ? (
            <div className="flex flex-wrap gap-1.5">
              {tools.slice(0, 4).map((tool) => (
                <Badge
                  key={`${agent.name}-${tool}`}
                  variant="outline"
                  className="bg-background/50 px-2 py-0 text-[10px] font-normal text-muted-foreground"
                >
                  {tool}
                </Badge>
              ))}
              {tools.length > 4 ? (
                <Badge variant="outline" className="bg-background/50 px-2 py-0 text-[10px] text-muted-foreground">
                  +{tools.length - 4}
                </Badge>
              ) : null}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground/50 italic">No tools assigned</p>
          )}
        </div>
      </CardContent>

      <CardFooter className="border-t bg-muted/10 p-3">
        <Button
          variant={isSelected ? 'default' : 'ghost'}
          size="sm"
          className={cn(
            "w-full justify-between gap-2 text-xs",
            !isSelected && "text-muted-foreground hover:text-foreground"
          )}
          onClick={(event) => {
            event.stopPropagation();
            onSelect(agent.name);
          }}
        >
          <span>{isSelected ? 'Active Session' : 'Start Session'}</span>
          <ArrowUpRight className="h-3 w-3" />
        </Button>
      </CardFooter>
    </Card>
  );
}

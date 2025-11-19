// File Path: features/chat/components/AgentSwitcher.tsx
// Description: Agent selection control for the chat workspace header.

'use client';

import { useMemo } from 'react';

import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import type { AgentSummary } from '@/types/agents';

interface AgentSwitcherProps {
  agents: AgentSummary[];
  selectedAgent: string;
  onChange: (agentName: string) => void;
  isLoading: boolean;
  error?: Error | null;
  className?: string;
}

export function AgentSwitcher({
  agents,
  selectedAgent,
  onChange,
  isLoading,
  error,
  className,
}: AgentSwitcherProps) {
  const currentAgent = useMemo(
    () => agents.find((agent) => agent.name === selectedAgent) ?? agents[0],
    [agents, selectedAgent],
  );

  if (isLoading) {
    return (
      <div className={className}>
        <Skeleton className="h-10 w-full rounded-md" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={className}>
        <Label className="text-xs uppercase tracking-[0.3em] text-destructive">Agent inventory</Label>
        <p className="mt-2 text-sm text-destructive/80">
          {error.message || 'Unable to load agents'}
        </p>
      </div>
    );
  }

  if (!agents.length) {
    return (
      <div className={className}>
        <Label className="text-xs uppercase tracking-[0.3em] text-foreground/50">Agent inventory</Label>
        <p className="mt-2 text-sm text-foreground/60">No agents available.</p>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="flex items-center justify-between">
        <div>
          <Label className="text-xs uppercase tracking-[0.3em] text-foreground/50">Agent</Label>
          <p className="text-sm text-foreground/60">
            {currentAgent?.description ?? 'Select which specialist should respond.'}
          </p>
        </div>
        {currentAgent ? (
          <Badge variant={currentAgent.status === "active" ? "default" : "secondary"} className="capitalize">
            {currentAgent.status}
          </Badge>
        ) : null}
      </div>

      <div className="mt-3">
        <Select value={selectedAgent} onValueChange={onChange}>
          <SelectTrigger className="bg-white/5 text-sm text-foreground">
            <SelectValue placeholder='Choose an agent' />
          </SelectTrigger>
          <SelectContent>
            {agents.map((agent) => (
              <SelectItem key={agent.name} value={agent.name} className="capitalize">
                <div className="flex flex-col gap-0.5">
                  <span className="font-medium text-foreground">{agent.name.replace('_', ' ')}</span>
                  {agent.description ? (
                    <span className="text-xs text-muted-foreground">{agent.description}</span>
                  ) : null}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}

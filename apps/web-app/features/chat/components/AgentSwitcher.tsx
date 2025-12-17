// File Path: features/chat/components/AgentSwitcher.tsx
// Description: Agent selection control with integrated insights and actions.

'use client';

import { useMemo } from 'react';
import { Bot, Sparkles, Info } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectItemTitle,
  SelectItemDescription,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import type { AgentSummary } from '@/types/agents';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface AgentSwitcherProps {
  agents: AgentSummary[];
  selectedAgent: string;
  onChange: (agentName: string) => void;
  isLoading: boolean;
  error?: Error | null;
  onShowInsights?: () => void;
  onShowDetails?: () => void;
  hasConversation?: boolean;
  className?: string;
}

export function AgentSwitcher({
  agents,
  selectedAgent,
  onChange,
  isLoading,
  error,
  onShowInsights,
  onShowDetails,
  hasConversation,
  className,
}: AgentSwitcherProps) {
  const currentAgent = useMemo(
    () => agents.find((agent) => agent.name === selectedAgent) ?? agents[0],
    [agents, selectedAgent],
  );

  if (isLoading) {
    return (
      <div className={cn("space-y-3", className)}>
        <div className="flex items-center justify-between">
           <Skeleton className="h-4 w-20" />
           <Skeleton className="h-8 w-8 rounded-md" />
        </div>
        <Skeleton className="h-10 w-full rounded-md" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("rounded-md border border-destructive/20 bg-destructive/10 p-3", className)}>
        <p className="text-xs font-medium text-destructive">Agent inventory unavailable</p>
        <p className="text-[10px] text-destructive/80 mt-1">{error.message}</p>
      </div>
    );
  }

  if (!agents.length) {
    return (
      <div className={className}>
        <p className="text-sm text-muted-foreground">No agents available.</p>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Bot className="h-4 w-4" />
          <span className="text-xs font-semibold uppercase tracking-wider">Agent</span>
        </div>
        <div className="flex items-center gap-1">
            {currentAgent && (
                <Badge 
                    variant={currentAgent.status === "active" ? "default" : "secondary"} 
                    className="mr-2 h-5 px-1.5 text-[10px] uppercase tracking-wider"
                >
                    {currentAgent.status}
                </Badge>
            )}
            
            <TooltipProvider>
              {onShowDetails && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-6 w-6 text-muted-foreground hover:text-primary disabled:opacity-30" 
                        disabled={!hasConversation}
                        onClick={onShowDetails}
                    >
                        <Info className="h-3.5 w-3.5" />
                        <span className="sr-only">Details</span>
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="top">Conversation Details</TooltipContent>
                </Tooltip>
              )}

              {onShowInsights && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-6 w-6 text-muted-foreground hover:text-primary" 
                        onClick={onShowInsights}
                    >
                        <Sparkles className="h-3.5 w-3.5" />
                        <span className="sr-only">Insights</span>
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="top">Agent Insights</TooltipContent>
                </Tooltip>
              )}
            </TooltipProvider>
        </div>
      </div>

      {/* Selector */}
      <Select value={selectedAgent} onValueChange={onChange}>
        <SelectTrigger className="w-full bg-white/5 text-left">
          <SelectValue placeholder="Choose an agent" />
        </SelectTrigger>
        <SelectContent>
          {agents.map((agent) => (
            <SelectItem key={agent.name} value={agent.name} className="capitalize">
              <div className="flex flex-col items-start text-left gap-0.5 py-0.5">
                <SelectItemTitle>{agent.name.replace('_', ' ')}</SelectItemTitle>
                {agent.description && (
                  <SelectItemDescription>{agent.description}</SelectItemDescription>
                )}
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}






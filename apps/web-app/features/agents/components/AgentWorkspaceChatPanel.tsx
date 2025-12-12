// File Path: features/agents/components/AgentWorkspaceChatPanel.tsx
// Description: Central chat canvas with agent switching + quick actions.

'use client';

import { Button } from '@/components/ui/button';
import type { AgentSummary } from '@/types/agents';
import { ChatControllerProvider } from '@/lib/chat';
import type { UseChatControllerReturn } from '@/lib/chat';
import { AgentSwitcher, ChatInterface } from '@/features/chat';

interface AgentWorkspaceChatPanelProps {
  agents: AgentSummary[];
  agentsError: Error | null;
  isLoadingAgents: boolean;
  selectedAgent: string;
  onSelectAgent: (agentName: string) => void;
  currentConversationId: string | null;
  onClearError: () => void;
  onSendMessage: (message: string) => Promise<void>;
  onStartNewConversation: () => void;
  onShowConversationDetail: () => void;
  shareLocation?: boolean;
  locationHint?: {
    city?: string | null;
    region?: string | null;
    country?: string | null;
    timezone?: string | null;
  };
  onShareLocationChange?: (value: boolean) => void;
  onLocationHintChange?: (
    field: 'city' | 'region' | 'country' | 'timezone',
    value: string,
  ) => void;
  chatController: UseChatControllerReturn;
}

export function AgentWorkspaceChatPanel({
  agents,
  agentsError,
  isLoadingAgents,
  selectedAgent,
  onSelectAgent,
  currentConversationId,
  onClearError,
  onSendMessage,
  onStartNewConversation,
  onShowConversationDetail,
  shareLocation = false,
  locationHint = {},
  onShareLocationChange,
  onLocationHintChange,
  chatController,
}: AgentWorkspaceChatPanelProps) {
  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <AgentSwitcher
          className="w-full lg:max-w-sm"
          agents={agents}
          selectedAgent={selectedAgent}
          onChange={onSelectAgent}
          isLoading={isLoadingAgents}
          error={agentsError}
        />
        <div className="flex flex-wrap gap-2">
          <Button
            variant="ghost"
            size="sm"
            disabled={!currentConversationId}
            onClick={onShowConversationDetail}
          >
            Details
          </Button>
          <Button variant="outline" size="sm" onClick={onStartNewConversation}>
            New chat
          </Button>
        </div>
      </div>

      <div className="flex-1 min-h-0 rounded-2xl border bg-muted/10 p-4">
        <ChatControllerProvider value={chatController}>
          <ChatInterface
            onSendMessage={onSendMessage}
            currentConversationId={currentConversationId}
            onClearConversation={onStartNewConversation}
            onClearError={onClearError}
            shareLocation={shareLocation}
            onShareLocationChange={onShareLocationChange ?? (() => {})}
            locationHint={locationHint}
            onLocationHintChange={onLocationHintChange ?? (() => {})}
            className="h-full"
          />
        </ChatControllerProvider>
      </div>
    </div>
  );
}

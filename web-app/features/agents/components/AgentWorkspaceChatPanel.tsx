// File Path: features/agents/components/AgentWorkspaceChatPanel.tsx
// Description: Central chat canvas with agent switching + quick actions.

'use client';

import { Button } from '@/components/ui/button';
import { ErrorState } from '@/components/ui/states';
import type { AgentSummary } from '@/types/agents';
import type { ChatMessage, ConversationLifecycleStatus, ToolState } from '@/lib/chat/types';
import { AgentSwitcher, ChatInterface } from '@/features/chat';

interface AgentWorkspaceChatPanelProps {
  agents: AgentSummary[];
  agentsError: Error | null;
  isLoadingAgents: boolean;
  selectedAgent: string;
  onSelectAgent: (agentName: string) => void;
  messages: ChatMessage[];
  isSending: boolean;
  isLoadingHistory: boolean;
  isClearingConversation: boolean;
  currentConversationId: string | null;
  errorMessage: string | null;
  onClearError: () => void;
  onSendMessage: (message: string) => Promise<void>;
  onStartNewConversation: () => void;
  onShowConversationDetail: () => void;
  tools: ToolState[];
  reasoningText: string;
  activeAgent: string;
  lifecycleStatus: ConversationLifecycleStatus;
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
}

export function AgentWorkspaceChatPanel({
  agents,
  agentsError,
  isLoadingAgents,
  selectedAgent,
  onSelectAgent,
  messages,
  isSending,
  isLoadingHistory,
  isClearingConversation,
  currentConversationId,
  errorMessage,
  onClearError,
  onSendMessage,
  onStartNewConversation,
  onShowConversationDetail,
  tools,
  reasoningText,
  activeAgent,
  lifecycleStatus,
  shareLocation = false,
  locationHint = {},
  onShareLocationChange,
  onLocationHintChange,
}: AgentWorkspaceChatPanelProps) {
  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
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
            variant="outline"
            size="sm"
            disabled={!currentConversationId}
            onClick={onShowConversationDetail}
          >
            Conversation details
          </Button>
          <Button variant="outline" size="sm" onClick={onStartNewConversation}>
            New conversation
          </Button>
        </div>
      </div>

      {errorMessage ? (
        <ErrorState
          title="Chat workspace error"
          message={errorMessage}
          onRetry={onClearError}
        />
      ) : null}

      <ChatInterface
        messages={messages}
        onSendMessage={onSendMessage}
        isSending={isSending}
        currentConversationId={currentConversationId}
        onClearConversation={onStartNewConversation}
        isClearingConversation={isClearingConversation}
        isLoadingHistory={isLoadingHistory}
        tools={tools}
        reasoningText={reasoningText}
        activeAgent={activeAgent}
        lifecycleStatus={lifecycleStatus}
        shareLocation={shareLocation}
        onShareLocationChange={onShareLocationChange ?? (() => {})}
        locationHint={locationHint}
        onLocationHintChange={onLocationHintChange ?? (() => {})}
        runOptions={{
          maxTurns: undefined,
          previousResponseId: undefined,
          handoffInputFilter: undefined,
          runConfigRaw: '',
        }}
        onRunOptionsChange={() => {}}
        className="min-h-[520px]"
      />
    </div>
  );
}

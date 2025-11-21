// File Path: features/agents/components/AgentWorkspaceChatPanel.tsx
// Description: Central chat canvas with agent switching + quick actions.

'use client';

import { useMemo } from 'react';

import { Button } from '@/components/ui/button';
import { InlineTag, SectionHeader } from '@/components/ui/foundation';
import { ErrorState } from '@/components/ui/states';
import type { AgentSummary } from '@/types/agents';
import type { ChatMessage } from '@/lib/chat/types';
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
}: AgentWorkspaceChatPanelProps) {
  const activeAgents = useMemo(() => agents.filter((agent) => agent.status === 'active').length, [agents]);
  const selectedAgentLabel = useMemo(() => selectedAgent.replace(/_/g, ' '), [selectedAgent]);

  return (
    <div className="space-y-4">
      <SectionHeader
        eyebrow="Workspace"
        title="Agent chat"
        description={
          currentConversationId
            ? `Conversation ${currentConversationId.substring(0, 12)}…`
            : 'Start a new conversation to brief your agent.'
        }
        actions={
          <InlineTag tone={agentsError ? 'warning' : activeAgents ? 'positive' : 'default'}>
            {isLoadingAgents
              ? 'Loading agents…'
              : agentsError
                ? 'Inventory unavailable'
                : `${activeAgents}/${agents.length || 0} active`}
          </InlineTag>
        }
      />

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
        className="min-h-[520px]"
      />

      <p className="text-xs text-foreground/50">
        Selected agent: <span className="font-semibold text-foreground">{selectedAgentLabel}</span>
      </p>
    </div>
  );
}

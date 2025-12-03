// File Path: features/chat/ChatWorkspace.tsx
// Description: Client-side orchestrator for the chat workspace.

'use client';

import { useEffect, useState } from 'react';

import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { ErrorState } from '@/components/ui/states';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { ConversationDetailDrawer } from '@/components/shared/conversations/ConversationDetailDrawer';

import { AgentSwitcher } from './components/AgentSwitcher';
import { BillingEventsPanel } from './components/BillingEventsPanel';
import { ChatInterface } from './components/ChatInterface';
import { ConversationSidebar } from './components/ConversationSidebar';
import { ToolMetadataPanel } from './components/ToolMetadataPanel';
import { CHAT_COPY } from './constants';
import { useChatWorkspace } from './hooks/useChatWorkspace';
import { formatConversationLabel } from './utils/formatters';
import { ChatControllerProvider } from '@/lib/chat';

export function ChatWorkspace() {
  const [insightsTab, setInsightsTab] = useState<'tools' | 'billing'>('tools');
  const {
    conversationList,
    isLoadingConversations,
    loadMoreConversations: loadMore,
    hasNextConversationPage: hasNextPage,
    billingEvents,
    billingStreamStatus,
    agents,
    isLoadingAgents,
    agentsError,
    errorMessage,
    currentConversationId,
    selectedAgent,
    selectedAgentLabel,
    toolDrawerOpen,
    setToolDrawerOpen,
    detailDrawerOpen,
    setDetailDrawerOpen,
    isLoadingTools,
    tools,
    toolsError,
    refetchTools,
    activeAgents,
    handleSelectConversation,
    handleNewConversation,
    handleDeleteConversation,
    handleWorkspaceError,
    sendMessage,
    shareLocation,
    setShareLocation,
    locationHint,
    updateLocationField,
    setSelectedAgent,
    chatController,
  } = useChatWorkspace();

  useEffect(() => {
    handleWorkspaceError();
  }, [handleWorkspaceError]);

  useEffect(() => {
    if (!currentConversationId) {
      setDetailDrawerOpen(false);
    }
  }, [currentConversationId, setDetailDrawerOpen]);

  return (
    <>
      <Sheet open={toolDrawerOpen} onOpenChange={setToolDrawerOpen}>
        <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Insights</SheetTitle>
            <SheetDescription>{CHAT_COPY.toolDrawer.description(selectedAgentLabel)}</SheetDescription>
          </SheetHeader>
          <Tabs value={insightsTab} onValueChange={(value) => setInsightsTab(value as 'tools' | 'billing')} className="mt-4">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="tools">Tools</TabsTrigger>
              <TabsTrigger value="billing">Billing</TabsTrigger>
            </TabsList>
            <TabsContent value="tools" className="mt-4 space-y-4">
              <ToolMetadataPanel
                selectedAgent={selectedAgentLabel}
                tools={tools}
                isLoading={isLoadingTools}
                error={toolsError}
                onRefresh={refetchTools}
              />
            </TabsContent>
            <TabsContent value="billing" className="mt-4">
              <BillingEventsPanel events={billingEvents} status={billingStreamStatus} />
            </TabsContent>
          </Tabs>
        </SheetContent>
      </Sheet>

      <div className="grid min-h-[70vh] gap-6 lg:grid-cols-[minmax(0,1.9fr)_minmax(320px,1fr)]">
        <div className="flex flex-col gap-4">
          <SectionHeader
            eyebrow={CHAT_COPY.header.eyebrow}
            title={CHAT_COPY.header.title}
            description={formatConversationLabel(currentConversationId)}
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

          {errorMessage ? <ErrorState message={errorMessage} /> : null}

          <ChatControllerProvider value={chatController}>
            <ChatInterface
              onSendMessage={sendMessage}
              currentConversationId={currentConversationId}
              onClearConversation={
                currentConversationId
                  ? () => {
                      void handleDeleteConversation(currentConversationId);
                    }
                  : undefined
              }
              shareLocation={shareLocation}
              onShareLocationChange={setShareLocation}
              locationHint={locationHint}
              onLocationHintChange={updateLocationField}
              className="h-[78vh]"
            />
          </ChatControllerProvider>
        </div>

        <div className="grid h-full gap-4 xl:grid-rows-[auto_1fr]">
          <GlassPanel className="p-4">
            <AgentSwitcher
              className="w-full"
              agents={agents}
              selectedAgent={selectedAgent}
              onChange={setSelectedAgent}
              isLoading={isLoadingAgents}
              error={agentsError}
              onShowInsights={() => setToolDrawerOpen(true)}
              onShowDetails={() => setDetailDrawerOpen(true)}
              hasConversation={!!currentConversationId}
            />
          </GlassPanel>

          <ConversationSidebar
            conversationList={conversationList}
            isLoadingConversations={isLoadingConversations}
            loadMoreConversations={loadMore}
            hasNextConversationPage={hasNextPage}
            currentConversationId={currentConversationId}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversation}
            onDeleteConversation={handleDeleteConversation}
            className="h-full"
          />
        </div>
      </div>

      <ConversationDetailDrawer
        open={detailDrawerOpen}
        onClose={() => setDetailDrawerOpen(false)}
        conversationId={currentConversationId}
        onDeleteConversation={handleDeleteConversation}
      />
    </>
  );
}

// File Path: features/chat/ChatWorkspace.tsx
// Description: Client-side orchestrator for the chat workspace.

'use client';

import { useEffect, useState } from 'react';
import { PanelRightOpen, PanelRightClose } from 'lucide-react';

import { GlassPanel, InlineTag } from '@/components/ui/foundation';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

import { ConversationDetailDrawer } from '@/components/shared/conversations/ConversationDetailDrawer';

import { AgentSwitcher } from './components/AgentSwitcher';
import { BillingEventsPanel } from './components/BillingEventsPanel';
import { ChatInterface } from './components/ChatInterface';
import { ConversationSidebar } from './components/conversation-sidebar';
import { ToolMetadataPanel } from './components/ToolMetadataPanel';
import { CHAT_COPY } from './constants';
import { useChatWorkspace } from './hooks/useChatWorkspace';
import { formatConversationLabel } from './utils/formatters';
import { ChatControllerProvider } from '@/lib/chat';

export function ChatWorkspace() {
  const [insightsTab, setInsightsTab] = useState<'tools' | 'billing'>('tools');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
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
    historyError,
    clearHistoryError,
    clearError,
    retryMessages,
    currentConversationId,
    currentConversationTitle,
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
    guardrailEvents,
    hasOlderMessages,
    isFetchingOlderMessages,
    loadOlderMessages,
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

      {/* Main Layout Container - Flex row to manage sidebar transition smoothly */}
      <div className="flex min-h-0 flex-1 gap-4 overflow-hidden">
        
        {/* Chat Interface (Flex Grow) */}
        <div className="flex min-h-0 flex-1 min-w-0 flex-col overflow-hidden transition-all duration-300 ease-in-out">
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
              className="h-full min-h-0"
              hasOlderMessages={hasOlderMessages}
              isLoadingOlderMessages={isFetchingOlderMessages}
              onLoadOlderMessages={loadOlderMessages}
              onRetryMessages={retryMessages}
              historyError={historyError}
              errorMessage={errorMessage}
              onClearHistory={clearHistoryError}
              onClearError={clearError}
              guardrailEvents={guardrailEvents}
              headerProps={{
                eyebrow: CHAT_COPY.header.eyebrow,
                title: CHAT_COPY.header.title,
                description: formatConversationLabel(currentConversationId, currentConversationTitle),
                actions: (
                  <div className="flex items-center gap-2">
                    <InlineTag tone={agentsError ? 'warning' : activeAgents ? 'positive' : 'default'}>
                      {isLoadingAgents
                        ? 'Loading agents…'
                        : agentsError
                          ? 'Inventory unavailable'
                          : `${activeAgents}/${agents.length || 0} active`}
                    </InlineTag>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:text-foreground"
                      onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                      title={isSidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}
                    >
                      {isSidebarOpen ? <PanelRightClose className="h-5 w-5" /> : <PanelRightOpen className="h-5 w-5" />}
                    </Button>
                  </div>
                ),
              }}
            />
          </ChatControllerProvider>
        </div>

        {/* Right Sidebar (Collapsible) */}
        <div 
            className={cn(
                "relative flex-shrink-0 transition-[width,opacity,transform] duration-300 ease-in-out",
                isSidebarOpen ? "w-[320px] opacity-100 translate-x-0" : "w-0 opacity-0 translate-x-10"
            )}
        >
           <div className="w-[320px] min-h-0 flex flex-1 flex-col">
              <GlassPanel className="flex min-h-0 flex-1 flex-col overflow-hidden border-l border-white/10 bg-background/40 p-0 backdrop-blur-xl">
                {/* Agent Switcher Section */}
                <div className="p-4 border-b border-white/5">
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
                </div>

                {/* Conversation List Section */}
                <ConversationSidebar
                  conversationList={conversationList}
                  isLoadingConversations={isLoadingConversations}
                  loadMoreConversations={loadMore}
                  hasNextConversationPage={hasNextPage}
                  currentConversationId={currentConversationId}
                  onSelectConversation={handleSelectConversation}
                  onNewConversation={handleNewConversation}
                  onDeleteConversation={handleDeleteConversation}
                  className="min-h-0 flex-1 border-none bg-transparent"
                  variant="embedded"
                />
              </GlassPanel>
           </div>
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

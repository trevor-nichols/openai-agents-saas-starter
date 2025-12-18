'use client';

import { useState } from 'react';
import { Terminal, History, Activity, FileText } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { InlineTag } from '@/components/ui/foundation';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Conversation, ConversationContent, ConversationScrollButton } from '@/components/ui/ai/conversation';
import type {
  PublicSseEvent,
  WorkflowRunDetail,
  WorkflowSummary,
} from '@/lib/api/client/types.gen';
import { WORKFLOW_STATUS_FILTERS, type StreamStatus, type WorkflowStatusFilter } from '../../constants';
import type { WorkflowRunListItemView } from '@/lib/workflows/types';

import type { WorkflowRunSummary, WorkflowStreamEventWithReceivedAt } from '../../types';

import { WorkflowStreamLog } from './streaming/WorkflowStreamLog';
import { WorkflowLiveStream } from './streaming/WorkflowLiveStream';
import { WorkflowRunsList } from './history/WorkflowRunsList';
import { WorkflowRunConversation } from './transcript/WorkflowRunConversation';
import { WorkflowRunDeleteButton } from './actions/WorkflowRunDeleteButton';
import { WorkflowFinalOutput } from './final/WorkflowFinalOutput';

interface WorkflowRunFeedProps {
  // Console Props
  workflows: WorkflowSummary[];
  streamEvents: WorkflowStreamEventWithReceivedAt[];
  streamStatus: StreamStatus;
  runError: string | null;
  isMockMode: boolean;
  onSimulate?: () => void;
  lastRunSummary: WorkflowRunSummary | null;
  lastUpdated: string | null;
  selectedRunId: string | null;
  
  // Transcript/Detail Props
  runDetail: WorkflowRunDetail | null;
  runReplayEvents: PublicSseEvent[] | null | undefined;
  isLoadingRun: boolean;
  isLoadingReplay: boolean;
  onCancelRun: () => void;
  cancelPending: boolean;
  onDeleteRun: (runId: string) => void;
  deletingRunId: string | null;

  // History Props
  historyRuns: WorkflowRunListItemView[];
  historyStatusFilter: WorkflowStatusFilter;
  onHistoryStatusChange: (value: WorkflowStatusFilter) => void;
  onHistoryRefresh: () => void;
  onHistoryLoadMore?: () => void;
  historyHasMore: boolean;
  isHistoryLoading: boolean;
  isHistoryFetchingMore: boolean;
  onSelectRun: (runId: string, workflowKey?: string | null) => void;
}

export function WorkflowRunFeed({
  workflows,
  streamEvents,
  streamStatus,
  runError,
  isMockMode,
  onSimulate,
  lastRunSummary,
  lastUpdated,
  selectedRunId,
  runDetail,
  runReplayEvents,
  isLoadingRun,
  isLoadingReplay,
  onCancelRun,
  cancelPending,
  onDeleteRun,
  deletingRunId,
  historyRuns,
  historyStatusFilter,
  onHistoryStatusChange,
  onHistoryRefresh,
  onHistoryLoadMore,
  historyHasMore,
  isHistoryLoading,
  isHistoryFetchingMore,
  onSelectRun,
}: WorkflowRunFeedProps) {
  const [activeTab, setActiveTab] = useState<'console' | 'final' | 'history'>('console');
  const [isTranscriptOpen, setIsTranscriptOpen] = useState(false);
  const [debugOpen, setDebugOpen] = useState(false);

  const transcriptOpen = isTranscriptOpen && Boolean(selectedRunId);
  const handleTranscriptToggle = (open: boolean) => {
    if (!open) {
      setIsTranscriptOpen(false);
      return;
    }
    if (selectedRunId) {
      setIsTranscriptOpen(true);
    }
  };

  return (
    <div className="flex h-full flex-col bg-background">
      <Tabs
        value={activeTab}
        onValueChange={(v) => setActiveTab(v as 'console' | 'final' | 'history')}
        className="flex h-full flex-col"
      >
        <div className="px-4 pt-3 pb-2 border-b flex items-center justify-between bg-muted/5">
          <TabsList className="h-8">
            <TabsTrigger value="console" className="h-7 text-xs gap-2">
              <Terminal className="h-3.5 w-3.5" />
              Console
            </TabsTrigger>
            <TabsTrigger value="final" className="h-7 text-xs gap-2">
              <FileText className="h-3.5 w-3.5" />
              Final
            </TabsTrigger>
            <TabsTrigger value="history" className="h-7 text-xs gap-2">
              <History className="h-3.5 w-3.5" />
              History
            </TabsTrigger>
          </TabsList>
          
          {activeTab !== 'history' && (
             <Sheet open={transcriptOpen} onOpenChange={handleTranscriptToggle}>
                <SheetTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-7 text-xs" disabled={!selectedRunId}>
                        <Activity className="h-3.5 w-3.5 mr-1" /> Transcript
                    </Button>
                </SheetTrigger>
                <SheetContent side="right" className="flex w-full flex-col overflow-hidden sm:max-w-xl">
                <SheetHeader>
                    <SheetTitle>Run transcript</SheetTitle>
                    <SheetDescription>Displays step outputs as a conversation.</SheetDescription>
                </SheetHeader>
                    {/* Transcript content */}
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                        {selectedRunId ? <InlineTag tone="default">Run: {selectedRunId}</InlineTag> : null}
                        {runDetail?.status ? <InlineTag tone="default">Status: {runDetail.status}</InlineTag> : null}
                        {runDetail?.status === 'running' ? (
                        <Button size="sm" variant="outline" onClick={onCancelRun} disabled={cancelPending}>
                            {cancelPending ? 'Canceling…' : 'Cancel run'}
                        </Button>
                        ) : null}
                        {runDetail ? (
                        <WorkflowRunDeleteButton
                            onConfirm={() => onDeleteRun(runDetail.workflow_run_id)}
                            pending={deletingRunId === runDetail.workflow_run_id}
                            tooltip="Delete run"
                        />
                        ) : null}
                    </div>
                    <div className="mt-4 flex min-h-0 flex-1 pr-2">
                      <WorkflowRunConversation
                        run={runDetail ?? null}
                        replayEvents={runReplayEvents ?? null}
                        isLoadingRun={isLoadingRun}
                        isLoadingReplay={isLoadingReplay}
                        className="min-h-0 flex-1"
                      />
                    </div>
                </SheetContent>
             </Sheet>
          )}
        </div>

        {/* CONSOLE TAB */}
        <TabsContent value="console" className="flex-1 min-h-0 data-[state=active]:flex flex-col m-0 p-0">
            <Conversation className="flex-1">
                <ConversationContent className="space-y-4 p-4">
                    {/* Status Messages */}
                    {streamStatus === 'completed' && (
                        <div className="rounded-md border border-emerald-900/50 bg-emerald-900/10 px-3 py-2 text-xs text-emerald-600 dark:text-emerald-400">
                            Workflow run completed successfully.
                        </div>
                    )}
                    {streamStatus === 'error' && !runError && (
                        <div className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive">
                            Workflow run ended with an error. Check the event log below.
                        </div>
                    )}
                    {isMockMode && (
                        <div className="flex items-center justify-between rounded-md border border-muted bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
                            <span>Mock mode: emit a sample event stream.</span>
                            <Button size="sm" variant="ghost" onClick={onSimulate} className="h-6 text-[10px]">
                                Simulate
                            </Button>
                        </div>
                    )}

                    {/* Summary Card */}
                    {lastRunSummary && (
                        <div className="rounded-md border bg-card p-3 shadow-sm space-y-2">
                            <div className="flex flex-wrap gap-2 text-xs">
                                <span className="font-semibold text-foreground">
                                    {workflows.find((w) => w.key === lastRunSummary.workflowKey)?.display_name ?? lastRunSummary.workflowKey}
                                </span>
                                {lastRunSummary.runId && (
                                    <span className="text-muted-foreground font-mono">#{lastRunSummary.runId.slice(-6)}</span>
                                )}
                            </div>
                            {lastRunSummary.message && (
                                <p className="text-xs text-muted-foreground italic">&quot;{lastRunSummary.message}&quot;</p>
                            )}
                            {lastUpdated && (
                                <p className="text-[10px] text-muted-foreground/50 text-right">
                                    {new Date(lastUpdated).toLocaleTimeString()}
                                </p>
                            )}
                        </div>
                    )}

                    {/* Stream Log */}
                    <WorkflowLiveStream events={streamEvents} />

                    <Collapsible open={debugOpen} onOpenChange={setDebugOpen}>
                      <div className="flex items-center justify-between">
                        <div className="text-xs font-semibold uppercase tracking-wide text-foreground/60">
                          Debug events
                        </div>
                        <CollapsibleTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-7 text-xs">
                            {debugOpen ? 'Hide' : 'Show'}
                          </Button>
                        </CollapsibleTrigger>
                      </div>
                      <CollapsibleContent className="mt-3">
                        <WorkflowStreamLog events={streamEvents} />
                      </CollapsibleContent>
                    </Collapsible>
                </ConversationContent>
                <ConversationScrollButton />
            </Conversation>
        </TabsContent>

        {/* FINAL OUTPUT TAB */}
        <TabsContent value="final" className="flex-1 min-h-0 data-[state=active]:flex flex-col m-0 p-0">
          <ScrollArea className="flex-1 min-h-0">
            <WorkflowFinalOutput
              selectedRunId={selectedRunId}
              runDetail={runDetail}
              replayEvents={runReplayEvents ?? null}
              streamEvents={streamEvents}
            />
          </ScrollArea>
        </TabsContent>

        {/* HISTORY TAB */}
        <TabsContent value="history" className="flex-1 min-h-0 data-[state=active]:flex flex-col m-0 p-0">
            <div className="flex items-center gap-2 p-2 border-b bg-muted/5">
                <Select value={historyStatusFilter} onValueChange={(value) => onHistoryStatusChange(value as WorkflowStatusFilter)}>
                    <SelectTrigger className="h-7 text-xs w-[110px]">
                        <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                        {WORKFLOW_STATUS_FILTERS.map((value) => (
                          <SelectItem key={value} value={value}>
                            {value === 'all' ? 'All' : value.charAt(0).toUpperCase() + value.slice(1)}
                          </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
                <Button variant="ghost" size="sm" onClick={onHistoryRefresh} className="h-7 text-xs ml-auto">
                    Refresh
                </Button>
            </div>
            <ScrollArea className="flex-1 min-h-0 p-4">
                <WorkflowRunsList
                    runs={historyRuns}
                    workflows={workflows}
                    isLoading={isHistoryLoading}
                    isFetchingMore={isHistoryFetchingMore}
                    hasMore={historyHasMore}
                    onLoadMore={onHistoryLoadMore}
                    onSelectRun={onSelectRun}
                    selectedRunId={selectedRunId}
                    onRefresh={onHistoryRefresh}
                    onDeleteRun={onDeleteRun}
                    deletingRunId={deletingRunId}
                />
            </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}

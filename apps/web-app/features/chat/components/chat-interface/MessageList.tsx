import { Fragment, useMemo } from 'react';
import { MessageItem } from './MessageItem';
import { ToolEventsPanel } from './ToolEventsPanel';
import type { ChatMessage, ToolEventAnchors, ToolState } from '@/lib/chat/types';
import type { AgentToolStreamMap } from '@/lib/streams/publicSseV1/agentToolStreams';
import type { AttachmentState } from '../../hooks/useAttachmentResolver';
import { Separator } from '@/components/ui/separator';

interface MessageListProps {
  messages: ChatMessage[];
  tools: ToolState[];
  agentToolStreams?: AgentToolStreamMap;
  toolEventAnchors?: ToolEventAnchors;
  attachmentState: AttachmentState;
  onResolveAttachment: (objectId: string) => Promise<void>;
  isBusy: boolean;
  onCopyMessage: (text: string) => void;
  onDeleteMessage?: (messageId: string) => void | Promise<void>;
}

export function MessageList({
  messages,
  tools,
  agentToolStreams,
  toolEventAnchors,
  attachmentState,
  onResolveAttachment,
  isBusy,
  onCopyMessage,
  onDeleteMessage,
}: MessageListProps) {
  const toolById = useMemo(() => new Map(tools.map((tool) => [tool.id, tool])), [tools]);
  const messageIds = useMemo(() => new Set(messages.map((message) => message.id)), [messages]);
  const anchoredToolIds = useMemo(() => {
    const ids = new Set<string>();
    if (!toolEventAnchors) return ids;
    Object.entries(toolEventAnchors).forEach(([anchorId, toolIds]) => {
      if (!messageIds.has(anchorId)) return;
      toolIds.forEach((id) => ids.add(id));
    });
    return ids;
  }, [messageIds, toolEventAnchors]);
  const unanchoredTools = useMemo(
    () => tools.filter((tool) => !anchoredToolIds.has(tool.id)),
    [anchoredToolIds, tools],
  );

  return (
    <>
      {messages.map((message) => {
        if (message.kind === 'memory_checkpoint') {
          const strategy = message.checkpoint?.strategy;
          return (
            <div key={message.id} className="my-5 flex items-center gap-3">
              <Separator className="flex-1" />
              <div className="text-center text-xs text-muted-foreground">
                <div className="font-medium">Memory checkpoint</div>
                <div className="text-[11px]">
                  {strategy ? `Context ${strategy} applied` : 'Context compacted'}
                </div>
              </div>
              <Separator className="flex-1" />
            </div>
          );
        }

        const anchoredToolsForMessage = (toolEventAnchors?.[message.id] ?? [])
          .map((toolId) => toolById.get(toolId))
          .filter((tool): tool is ToolState => Boolean(tool));

        return (
          <Fragment key={message.id}>
            <MessageItem
              message={message}
              attachmentState={attachmentState}
              onResolveAttachment={onResolveAttachment}
              isBusy={isBusy}
              onCopy={onCopyMessage}
              onDeleteMessage={onDeleteMessage}
            />
            {anchoredToolsForMessage.length > 0 ? (
              <ToolEventsPanel tools={anchoredToolsForMessage} agentToolStreams={agentToolStreams} />
            ) : null}
          </Fragment>
        );
      })}

      {unanchoredTools.length > 0 ? (
        <ToolEventsPanel tools={unanchoredTools} agentToolStreams={agentToolStreams} />
      ) : null}
    </>
  );
}

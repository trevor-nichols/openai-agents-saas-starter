import { Fragment, useMemo } from 'react';
import { MessageItem } from './MessageItem';
import { ToolEventsPanel } from './ToolEventsPanel';
import type { ChatMessage, ToolEventAnchors, ToolState } from '@/lib/chat/types';
import type { AttachmentState } from '../../hooks/useAttachmentResolver';

interface MessageListProps {
  messages: ChatMessage[];
  tools: ToolState[];
  toolEventAnchors?: ToolEventAnchors;
  attachmentState: AttachmentState;
  onResolveAttachment: (objectId: string) => Promise<void>;
  isBusy: boolean;
  onCopyMessage: (text: string) => void;
}

export function MessageList({
  messages,
  tools,
  toolEventAnchors,
  attachmentState,
  onResolveAttachment,
  isBusy,
  onCopyMessage,
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
            />
            {anchoredToolsForMessage.length > 0 ? (
              <ToolEventsPanel tools={anchoredToolsForMessage} />
            ) : null}
          </Fragment>
        );
      })}

      {unanchoredTools.length > 0 ? <ToolEventsPanel tools={unanchoredTools} /> : null}
    </>
  );
}

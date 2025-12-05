import { InlineTag } from '@/components/ui/foundation';
import { Actions, Action } from '@/components/ui/ai/actions';
import { Loader } from '@/components/ui/ai/loader';
import { Message, MessageAvatar, MessageContent } from '@/components/ui/ai/message';
import { Response } from '@/components/ui/ai/response';
import { CodeBlock } from '@/components/ui/ai/code-block';
import { CopyIcon } from 'lucide-react';

import { formatClockTime } from '@/lib/utils/time';
import type { ChatMessage } from '@/lib/chat/types';
import type { AttachmentState } from '../../hooks/useAttachmentResolver';
import { MessageAttachments } from './MessageAttachments';
import { formatStructuredOutput } from '../../utils/formatters';

interface MessageItemProps {
  message: ChatMessage;
  onCopy: (text: string) => void;
  attachmentState: AttachmentState;
  onResolveAttachment: (objectId: string) => Promise<void>;
  isBusy: boolean;
}

export function MessageItem({ message, onCopy, attachmentState, onResolveAttachment, isBusy }: MessageItemProps) {
  return (
    <Message from={message.role}>
      <MessageContent>
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <InlineTag tone={message.role === 'user' ? 'positive' : 'default'}>
              {message.role === 'user' ? 'You' : 'Agent'}
            </InlineTag>
            {message.isStreaming ? (
              <div className="flex items-center gap-1 text-muted-foreground">
                <Loader size={14} />
                <span className="text-[11px] uppercase tracking-wide">Streaming</span>
              </div>
            ) : message.timestamp ? (
              <span className="text-[11px] uppercase tracking-wide text-foreground/50">
                {formatClockTime(message.timestamp)}
              </span>
            ) : (
              <span className="text-[11px] uppercase tracking-wide text-foreground/40">Pending</span>
            )}
          </div>
          <Actions>
            <Action tooltip="Copy message" label="Copy message" onClick={() => void onCopy(message.content)}>
              <CopyIcon size={14} />
            </Action>
          </Actions>
        </div>

        <Response className="mt-2 leading-relaxed" citations={message.citations ?? undefined}>
          {message.content}
        </Response>

        {message.structuredOutput ? (
          <div className="mt-3 space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-foreground/60">Structured output</p>
            <CodeBlock code={formatStructuredOutput(message.structuredOutput)} language="json" />
          </div>
        ) : null}

        {message.attachments && message.attachments.length > 0 ? (
          <MessageAttachments
            attachments={message.attachments}
            attachmentState={attachmentState}
            onResolve={onResolveAttachment}
            isBusy={isBusy}
          />
        ) : null}
      </MessageContent>
      <MessageAvatar src="" name={message.role === 'user' ? 'You' : 'Agent'} />
    </Message>
  );
}

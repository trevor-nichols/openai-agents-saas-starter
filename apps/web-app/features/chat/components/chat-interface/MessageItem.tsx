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
  const isUser = message.role === 'user';

  return (
    <Message from={message.role} className="mb-2">
      <div className="flex min-w-0 flex-col gap-1">
        <MessageContent>
          <Response className="leading-relaxed" citations={message.citations ?? undefined}>
            {message.content}
          </Response>

          {message.structuredOutput ? (
            <div className="mt-3 space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-foreground/60">
                Structured output
              </p>
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

        <div className="flex flex-row items-center gap-2 pl-1 pt-1 opacity-0 transition-opacity group-hover:opacity-100">
          {!isUser ? (
            <Actions>
              <Action tooltip="Copy message" label="Copy message" onClick={() => void onCopy(message.content)}>
                <CopyIcon size={14} />
              </Action>
            </Actions>
          ) : null}
          <div className="text-[10px] text-muted-foreground">
            {message.isStreaming ? (
              <div className="flex items-center gap-1 text-muted-foreground">
                <Loader size={12} />
                <span className="uppercase tracking-wide">Generating</span>
              </div>
            ) : message.timestamp ? (
              formatClockTime(message.timestamp)
            ) : null}
          </div>
        </div>
      </div>

      <MessageAvatar src="" name={isUser ? 'You' : 'Agent'} />
    </Message>
  );
}

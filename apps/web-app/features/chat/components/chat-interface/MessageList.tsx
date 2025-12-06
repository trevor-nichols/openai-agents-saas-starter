import { MessageItem } from './MessageItem';
import type { ChatMessage } from '@/lib/chat/types';
import type { AttachmentState } from '../../hooks/useAttachmentResolver';

interface MessageListProps {
  messages: ChatMessage[];
  attachmentState: AttachmentState;
  onResolveAttachment: (objectId: string) => Promise<void>;
  isBusy: boolean;
  onCopyMessage: (text: string) => void;
}

export function MessageList({ messages, attachmentState, onResolveAttachment, isBusy, onCopyMessage }: MessageListProps) {
  return (
    <>
      {messages.map((message) => (
        <MessageItem
          key={message.id}
          message={message}
          attachmentState={attachmentState}
          onResolveAttachment={onResolveAttachment}
          isBusy={isBusy}
          onCopy={onCopyMessage}
        />
      ))}
    </>
  );
}

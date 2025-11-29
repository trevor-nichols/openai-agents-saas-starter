import type { Meta, StoryObj } from '@storybook/react';

import { Conversation, ConversationContent, ConversationScrollButton } from './conversation';
import { Message, MessageAvatar, MessageContent } from './message';
import { Loader } from './loader';

const meta: Meta<typeof Conversation> = {
  title: 'AI/Conversation',
  component: Conversation,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Conversation>;

export const Scrollable: Story = {
  render: () => (
    <div className="h-72 w-full max-w-2xl border border-white/10 rounded-lg">
      <Conversation>
        <ConversationContent>
          {Array.from({ length: 8 }).map((_, i) => (
            <Message key={i} from={i % 2 === 0 ? 'user' : 'assistant'}>
              <MessageAvatar src={`https://avatar.vercel.sh/${i % 2 === 0 ? 'user' : 'ai'}`} name={i % 2 === 0 ? 'You' : 'AI'} />
              <MessageContent>
                {i % 2 === 0 ? `User message #${i + 1}` : `Assistant reply #${i + 1}`}
              </MessageContent>
            </Message>
          ))}
          <Message from="assistant">
            <MessageAvatar src="https://avatar.vercel.sh/ai" name="AI" />
            <MessageContent className="flex items-center gap-2">
              <Loader size={14} /> Typing...
            </MessageContent>
          </Message>
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>
    </div>
  ),
};

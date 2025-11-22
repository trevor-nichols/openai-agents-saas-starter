import type { Meta, StoryObj } from '@storybook/react';
import { Conversation, ConversationContent, ConversationScrollButton } from './conversation';
import { Message, MessageAvatar, MessageContent } from './message';
import { Response } from './response';

const meta: Meta<typeof Message> = {
  title: 'AI/Message',
  component: Message,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Message>;

export const ChatThread: Story = {
  render: () => (
    <div className="h-96 w-full max-w-3xl">
      <Conversation>
        <ConversationContent>
          <Message from="user">
            <MessageAvatar src="https://avatar.vercel.sh/user" name="You" />
            <MessageContent>How can I export my billing events to CSV?</MessageContent>
          </Message>
          <Message from="assistant">
            <MessageAvatar src="https://avatar.vercel.sh/ai" name="AI" />
            <MessageContent>
              <Response>
                {`Sure! Open Billing → Events and click “Export CSV”. You can also call the /billing/events API with format=csv.`}
              </Response>
            </MessageContent>
          </Message>
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>
    </div>
  ),
};

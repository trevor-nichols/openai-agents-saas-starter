import type { Meta, StoryObj } from '@storybook/react';
import { Conversation, ConversationContent, ConversationScrollButton } from './conversation';
import { Message, MessageAvatar, MessageContent } from './message';
import { Response } from './response';
import { CodeBlock } from './code-block';

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
              <div className="mt-3 space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wide text-foreground/60">Structured output</p>
                <CodeBlock
                  code={JSON.stringify({ action: 'export', format: 'csv', resource: 'billing_events' }, null, 2)}
                  language="json"
                />
              </div>
              <div className="mt-3 space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wide text-foreground/60">Attachments</p>
                <div className="rounded-md border border-white/5 bg-white/5 px-3 py-2 text-xs">
                  <div className="font-medium text-foreground">statement.pdf</div>
                  <div className="text-foreground/60">application/pdf • 245 KB</div>
                </div>
              </div>
            </MessageContent>
          </Message>
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>
    </div>
  ),
};

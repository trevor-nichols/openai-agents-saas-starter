import type { Meta, StoryObj } from '@storybook/react';
import { StoryProviders } from '../../../../.storybook/StoryProviders';
import { setConversationDetailMode } from '../../../../.storybook/mocks/conversations-queries';
import { setDeleteConversationHandler } from '../../../../.storybook/mocks/conversations-api';
import { ConversationDetailDrawer } from '../ConversationDetailDrawer';
import { conversationDetailFixture } from './fixtures';

const deleteCalls: string[] = [];
const recordDelete = async (id: string) => {
  deleteCalls.push(id);
};
const resetDeleteCalls = () => {
  deleteCalls.length = 0;
};

const ensureGlobals = () => {
  if (!(globalThis as any).navigator) {
    (globalThis as any).navigator = {} as Navigator;
  }
  if (!(globalThis as any).navigator.clipboard) {
    (globalThis as any).navigator.clipboard = {
      writeText: async () => {},
    };
  }
  if (!URL.createObjectURL) {
    URL.createObjectURL = () => 'blob:story-object';
  }
  if (!URL.revokeObjectURL) {
    URL.revokeObjectURL = () => {};
  }
};

ensureGlobals();

const meta = {
  title: 'Shared/ConversationDetailDrawer',
  component: ConversationDetailDrawer,
  args: {
    conversationId: conversationDetailFixture.conversation_id,
    open: true,
    onClose: () => {},
  },
  parameters: {
    layout: 'fullscreen',
  },
} satisfies Meta<typeof ConversationDetailDrawer>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Loading: Story = {
  render: (args) => {
    setConversationDetailMode('loading');
    return (
      <StoryProviders theme="dark">
        <div className="h-[720px] bg-background text-foreground">
          <ConversationDetailDrawer {...args} />
        </div>
      </StoryProviders>
    );
  },
};

export const Error: Story = {
  render: (args) => {
    setConversationDetailMode('error');
    return (
      <StoryProviders theme="dark">
        <div className="h-[720px] bg-background text-foreground">
          <ConversationDetailDrawer {...args} />
        </div>
      </StoryProviders>
    );
  },
};

export const Loaded: Story = {
  render: (args) => {
    setConversationDetailMode('loaded');
    resetDeleteCalls();
    setDeleteConversationHandler(recordDelete);
    return (
      <StoryProviders theme="dark">
        <div className="h-[720px] bg-background text-foreground">
          <ConversationDetailDrawer
            {...args}
            onDeleted={() => {}}
            onClose={() => {}}
            onDeleteConversation={async (id) => recordDelete(id)}
          />
        </div>
      </StoryProviders>
    );
  },
};

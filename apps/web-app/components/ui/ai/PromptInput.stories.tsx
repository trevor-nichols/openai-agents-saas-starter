import type { Meta, StoryObj } from '@storybook/react';
import { Paperclip, Sparkles } from 'lucide-react';

import {
  PromptInput,
  PromptInputButton,
  PromptInputModelSelect,
  PromptInputModelSelectContent,
  PromptInputModelSelectItem,
  PromptInputModelSelectTrigger,
  PromptInputModelSelectValue,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
  PromptInputTools,
} from './prompt-input';

const meta: Meta<typeof PromptInput> = {
  title: 'AI/PromptInput',
  component: PromptInput,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof PromptInput>;

export const Default: Story = {
  render: () => (
    <PromptInput className="max-w-3xl">
      <PromptInputTextarea />
      <PromptInputToolbar>
        <PromptInputTools>
          <PromptInputButton variant="ghost">
            <Paperclip className="h-4 w-4" />
            Attach
          </PromptInputButton>
          <PromptInputButton variant="ghost">
            <Sparkles className="h-4 w-4" />
            Improve
          </PromptInputButton>
        </PromptInputTools>
        <div className="flex items-center gap-2">
          <PromptInputModelSelect defaultValue="gpt-5.1">
            <PromptInputModelSelectTrigger aria-label="Select model">
              <PromptInputModelSelectValue placeholder="Model" />
            </PromptInputModelSelectTrigger>
            <PromptInputModelSelectContent>
              <PromptInputModelSelectItem value="gpt-5.1">gpt-5.1</PromptInputModelSelectItem>
              <PromptInputModelSelectItem value="gpt-4.1-mini">gpt-4.1-mini</PromptInputModelSelectItem>
            </PromptInputModelSelectContent>
          </PromptInputModelSelect>
          <PromptInputSubmit status="submitted" />
        </div>
      </PromptInputToolbar>
    </PromptInput>
  ),
};

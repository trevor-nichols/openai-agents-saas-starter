import type { Meta, StoryObj } from '@storybook/react';

import { Suggestion, Suggestions } from '../../ai/suggestion';

const meta: Meta<typeof Suggestions> = {
  title: 'AI/Suggestions',
  component: Suggestions,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Suggestions>;

export const Default: Story = {
  render: () => (
    <Suggestions>
      {['Summarize this chat', 'Generate SLA PDF', 'Create onboarding checklist', 'Suggest follow-up email'].map(
        (text) => (
          <Suggestion key={text} suggestion={text} />
        )
      )}
    </Suggestions>
  ),
};

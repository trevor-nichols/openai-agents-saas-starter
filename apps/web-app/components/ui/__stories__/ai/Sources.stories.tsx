import type { Meta, StoryObj } from '@storybook/react';

import { Source, Sources, SourcesContent, SourcesTrigger } from '../../ai/source';

const meta: Meta<typeof Sources> = {
  title: 'AI/Sources',
  component: Sources,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Sources>;

const sampleSources = [
  { title: 'OpenAI Agents', href: 'https://platform.openai.com/docs/assistants' },
  { title: 'Stripe Billing', href: 'https://stripe.com/docs/billing' },
  { title: 'Postgres JSONB', href: 'https://www.postgresql.org/docs/current/datatype-json.html' },
];

export const Default: Story = {
  args: {
    defaultOpen: true,
  },
  render: (args) => (
    <Sources {...args}>
      <SourcesTrigger count={sampleSources.length} />
      <SourcesContent>
        {sampleSources.map((source) => (
          <Source key={source.href} href={source.href} title={source.title} />
        ))}
      </SourcesContent>
    </Sources>
  ),
};

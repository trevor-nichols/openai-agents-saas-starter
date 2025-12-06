import type { Meta, StoryObj } from '@storybook/react';

import {
  InlineCitation,
  InlineCitationCard,
  InlineCitationCardBody,
  InlineCitationCardTrigger,
  InlineCitationCarousel,
  InlineCitationCarouselContent,
  InlineCitationCarouselHeader,
  InlineCitationCarouselIndex,
  InlineCitationCarouselItem,
  InlineCitationCarouselPrev,
  InlineCitationCarouselNext,
  InlineCitationText,
} from './inline-citation';

const sources = [
  { title: 'OpenAI Agents Docs', url: 'https://platform.openai.com/docs/assistants' },
  { title: 'Stripe Billing', url: 'https://stripe.com/docs/billing' },
  { title: 'Postgres JSONB', url: 'https://www.postgresql.org/docs/current/datatype-json.html' },
];

const meta: Meta<typeof InlineCitation> = {
  title: 'AI/InlineCitation',
  component: InlineCitation,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof InlineCitation>;

export const Default: Story = {
  render: () => (
    <InlineCitation>
      <InlineCitationText>Billing export</InlineCitationText>
      <InlineCitationCard>
        <InlineCitationCardTrigger sources={sources.map((s) => s.url)} />
        <InlineCitationCardBody>
          <InlineCitationCarousel>
            <InlineCitationCarouselHeader>
              Sources
              <InlineCitationCarouselIndex />
            </InlineCitationCarouselHeader>
            <InlineCitationCarouselContent>
              {sources.map((source) => (
                <InlineCitationCarouselItem key={source.url}>
                  <p className="font-semibold text-sm">{source.title}</p>
                  <p className="text-xs text-muted-foreground break-all">{source.url}</p>
                </InlineCitationCarouselItem>
              ))}
            </InlineCitationCarouselContent>
            <div className="flex items-center justify-between px-4 pb-3">
              <InlineCitationCarouselPrev />
              <InlineCitationCarouselNext />
            </div>
          </InlineCitationCarousel>
        </InlineCitationCardBody>
      </InlineCitationCard>
    </InlineCitation>
  ),
};

import type { Meta, StoryObj } from '@storybook/react';

import { Marquee, MarqueeContent, MarqueeFade, MarqueeItem } from '../marquee';

const meta: Meta = {
  title: 'UI/Media/Marquee',
  parameters: {
    layout: 'padded',
  },
};

export default meta;

type Story = StoryObj<typeof meta>;

const logos = ['OpenAI', 'Stripe', 'Vercel', 'Datadog', 'Postgres', 'Redis', 'Sentry', 'Docker'];

export const Default: Story = {
  render: () => (
    <div className="relative w-full overflow-hidden rounded-xl border border-white/10 bg-white/5 p-4">
      <Marquee>
        <MarqueeContent speed={30}>
          {logos.map((logo) => (
            <MarqueeItem key={logo} className="text-sm font-semibold text-foreground/80">
              {logo}
            </MarqueeItem>
          ))}
        </MarqueeContent>
        <MarqueeFade side="left" />
        <MarqueeFade side="right" />
      </Marquee>
    </div>
  ),
};

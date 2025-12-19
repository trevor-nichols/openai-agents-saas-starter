import type { Meta, StoryObj } from '@storybook/react';

import { Response } from '../../ai/response';

const meta: Meta<typeof Response> = {
  title: 'AI/Response',
  component: Response,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Response>;

const markdown = `### Billing export\n- Go to **Billing → Events**\n- Click \`Export CSV\`\n- API: \`GET /api/billing/events?format=csv\`\n\n> Tip: filter by status=failed to triage issues faster.`;

export const Default: Story = {
  args: {
    children: markdown,
  },
};

export const WithMath: Story = {
  args: {
    children: 'Token cost: $0.002 per 1K tokens. For 142,000 tokens: $142{,}000 / 1000 × 0.002 = **$284**.',
  },
};

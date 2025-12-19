import type { Meta, StoryObj } from '@storybook/react';

import { StoryProviders } from '../../../.storybook/StoryProviders';
import { LogoutButton } from '../LogoutButton';

const mockFetch: typeof fetch = async () => new Response('{}', { status: 200 });

globalThis.fetch = mockFetch;

const meta = {
  title: 'Auth/LogoutButton',
  component: LogoutButton,
  parameters: {
    layout: 'centered',
  },
} satisfies Meta<typeof LogoutButton>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <StoryProviders theme="light">
      <div className="rounded-xl border border-border bg-card p-6 text-foreground shadow-xl">
        <LogoutButton />
      </div>
    </StoryProviders>
  ),
};

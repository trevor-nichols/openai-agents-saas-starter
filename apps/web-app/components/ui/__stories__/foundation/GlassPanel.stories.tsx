import type { Meta, StoryObj } from '@storybook/react';

import { GlassPanel } from '../../foundation/GlassPanel';

const meta: Meta<typeof GlassPanel> = {
  title: 'UI/Foundation/GlassPanel',
  component: GlassPanel,
  tags: ['autodocs'],
  args: {
    children: (
      <div className="space-y-2">
        <p className="text-sm text-foreground/80">Frosted container with blur and soft border.</p>
        <p className="text-sm text-foreground/60">Use for dashboards, stats, or light chrome surfaces.</p>
      </div>
    ),
  },
};

export default meta;

type Story = StoryObj<typeof GlassPanel>;

export const Default: Story = {};

export const WithTightPadding: Story = {
  args: {
    className: 'p-4',
  },
};

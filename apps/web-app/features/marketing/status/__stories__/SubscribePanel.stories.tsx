'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { SubscribePanel } from '../components/SubscribePanel';

const meta: Meta<typeof SubscribePanel> = {
  title: 'Marketing/Status/SubscribePanel',
  component: SubscribePanel,
  args: {
    rssHref: '/status/rss',
    onCtaClick: (meta) => console.log('cta click', meta),
  },
};

export default meta;

type Story = StoryObj<typeof SubscribePanel>;

export const Default: Story = {};

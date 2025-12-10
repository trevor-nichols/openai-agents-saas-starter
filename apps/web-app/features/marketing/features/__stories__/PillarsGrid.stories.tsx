'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { PillarsGrid } from '../components/PillarsGrid';
import { FEATURE_PILLARS } from '../constants';

const meta: Meta<typeof PillarsGrid> = {
  title: 'Marketing/Features/PillarsGrid',
  component: PillarsGrid,
  args: {
    pillars: FEATURE_PILLARS,
    onCtaClick: ({ location, cta }) => console.log('pillar cta', location, cta),
  },
};

export default meta;

type Story = StoryObj<typeof PillarsGrid>;

export const Default: Story = {};

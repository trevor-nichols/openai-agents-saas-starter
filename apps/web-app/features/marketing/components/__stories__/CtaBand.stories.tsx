'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { CtaBand } from '../CtaBand';
import { ctaConfig } from './fixtures';

const meta: Meta<typeof CtaBand> = {
  title: 'Marketing/Components/CtaBand',
  component: CtaBand,
  args: {
    config: ctaConfig,
    onCtaClick: (meta) => console.log('cta click', meta),
  },
};

export default meta;

type Story = StoryObj<typeof CtaBand>;

export const Default: Story = {};

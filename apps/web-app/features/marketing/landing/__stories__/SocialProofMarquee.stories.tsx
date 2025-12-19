'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { SocialProofMarquee } from '../components/SocialProofMarquee';
import { logos } from './fixtures';

const meta: Meta<typeof SocialProofMarquee> = {
  title: 'Marketing/Landing/SocialProofMarquee',
  component: SocialProofMarquee,
  args: {
    logos,
  },
};

export default meta;

type Story = StoryObj<typeof SocialProofMarquee>;

export const Default: Story = {};

export const Empty: Story = {
  args: {
    logos: [],
  },
};

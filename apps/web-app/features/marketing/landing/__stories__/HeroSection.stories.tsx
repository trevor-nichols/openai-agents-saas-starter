'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { HeroSection } from '../components/HeroSection';
import { heroCopy, statusSummary } from './fixtures';

const meta: Meta<typeof HeroSection> = {
  title: 'Marketing/Landing/HeroSection',
  component: HeroSection,
  args: {
    copy: heroCopy,
    statusSummary,
    onCtaClick: (meta) => console.log('hero cta', meta),
  },
};

export default meta;

type Story = StoryObj<typeof HeroSection>;

export const Default: Story = {};

export const WithoutStatus: Story = {
  args: {
    statusSummary: null,
  },
};

'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { TestimonialPanel } from '../components/TestimonialPanel';
import { FEATURES_TESTIMONIAL } from '../constants';

const meta: Meta<typeof TestimonialPanel> = {
  title: 'Marketing/Features/TestimonialPanel',
  component: TestimonialPanel,
  args: {
    testimonial: FEATURES_TESTIMONIAL,
  },
};

export default meta;

type Story = StoryObj<typeof TestimonialPanel>;

export const Default: Story = {};

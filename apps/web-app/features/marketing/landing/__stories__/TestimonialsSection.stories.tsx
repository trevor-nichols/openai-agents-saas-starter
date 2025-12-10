'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { TestimonialsSection } from '../components/TestimonialsSection';
import { testimonials } from './fixtures';

const meta: Meta<typeof TestimonialsSection> = {
  title: 'Marketing/Landing/TestimonialsSection',
  component: TestimonialsSection,
  args: {
    testimonials,
  },
};

export default meta;

type Story = StoryObj<typeof TestimonialsSection>;

export const Default: Story = {};

export const Empty: Story = {
  args: {
    testimonials: [],
  },
};

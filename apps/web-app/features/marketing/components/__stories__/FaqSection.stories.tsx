'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { FaqSection } from '../FaqSection';
import { faqItems } from './fixtures';

const meta: Meta<typeof FaqSection> = {
  title: 'Marketing/Components/FaqSection',
  component: FaqSection,
  args: {
    items: faqItems,
    columns: 2,
  },
};

export default meta;

type Story = StoryObj<typeof FaqSection>;

export const Default: Story = {};

'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { FeatureHighlightsGrid } from '../components/FeatureHighlightsGrid';
import { featureHighlights } from './fixtures';

const meta: Meta<typeof FeatureHighlightsGrid> = {
  title: 'Marketing/Landing/FeatureHighlightsGrid',
  component: FeatureHighlightsGrid,
  args: {
    highlights: featureHighlights,
  },
};

export default meta;

type Story = StoryObj<typeof FeatureHighlightsGrid>;

export const Default: Story = {};

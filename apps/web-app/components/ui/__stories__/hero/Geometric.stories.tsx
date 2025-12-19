import type { Meta, StoryObj } from '@storybook/react';

import { HeroGeometric } from '../../hero/Geometric';

const meta: Meta<typeof HeroGeometric> = {
  title: 'UI/Media/HeroGeometric',
  component: HeroGeometric,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;

type Story = StoryObj<typeof HeroGeometric>;

export const Default: Story = {
  args: {
    title1: 'Build with Agents',
    title2: 'Launch faster, safer',
    description: 'Composable UI primitives plus FastAPI + Next.js scaffolding to ship AI products quickly.',
    className: 'min-h-[70vh]',
  },
};

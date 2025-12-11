import type { Meta, StoryObj } from '@storybook/react';
import { Activity, TrendingUp } from 'lucide-react';

import { StatCard } from '../../foundation/StatCard';

const meta: Meta<typeof StatCard> = {
  title: 'UI/Foundation/StatCard',
  component: StatCard,
  tags: ['autodocs'],
  args: {
    label: 'Active Users',
    value: '12,480',
    helperText: 'Rolling 30d window',
    icon: <Activity className="h-5 w-5" />,
    trend: { value: '+8.3%', tone: 'positive', label: 'vs last month' },
  },
};

export default meta;

type Story = StoryObj<typeof StatCard>;

export const Default: Story = {};

export const NegativeTrend: Story = {
  args: {
    trend: { value: '-2.1%', tone: 'negative', label: 'vs last week' },
  },
};

export const WithCustomLayout: Story = {
  args: {
    className: 'md:flex-row md:items-center md:justify-between',
    helperText: 'Custom layout option for horizontal placement.',
    icon: <TrendingUp className="h-5 w-5" />,
  },
};

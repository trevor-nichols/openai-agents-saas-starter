import type { Meta, StoryObj } from '@storybook/react';
import { ArrowRight } from 'lucide-react';

import { Button } from '../button';
import { Magnetic } from '../../motion/Magnetic';

const meta: Meta<typeof Magnetic> = {
  title: 'UI/Motion/Magnetic',
  component: Magnetic,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Magnetic>;

export const Default: Story = {
  render: () => (
    <Magnetic strength={0.9} range={140}>
      <Button size="lg" className="rounded-full px-5">
        Explore
        <ArrowRight className="h-4 w-4" />
      </Button>
    </Magnetic>
  ),
};

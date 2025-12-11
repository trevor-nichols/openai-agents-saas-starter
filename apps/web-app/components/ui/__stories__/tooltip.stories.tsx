import type { Meta, StoryObj } from '@storybook/react';
import { Info } from 'lucide-react';

import { Button } from '../button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../tooltip';

const meta: Meta<typeof Tooltip> = {
  title: 'UI/Overlays/Tooltip',
  component: Tooltip,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
};

export default meta;

type Story = StoryObj<typeof Tooltip>;

export const Default: Story = {
  render: () => (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline" size="sm">
            <Info className="mr-2 h-4 w-4" />
            Hover me
          </Button>
        </TooltipTrigger>
        <TooltipContent>LLM usage updates every 60 seconds.</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  ),
};

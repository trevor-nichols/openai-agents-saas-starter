import type { Meta, StoryObj } from '@storybook/react';
import Image from 'next/image';

import { AspectRatio } from '../aspect-ratio';

const meta: Meta<typeof AspectRatio> = {
  title: 'UI/Core/AspectRatio',
  component: AspectRatio,
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof AspectRatio>;

export const VideoRatio: Story = {
  render: () => (
    <div className="w-[450px]">
      <AspectRatio ratio={16 / 9} className="bg-muted">
        <Image
          src="https://images.unsplash.com/photo-1588345921523-c2dcdb7f1dcd?w=800&dpr=2&q=80"
          alt="Photo by Drew Beamer"
          fill
          className="rounded-md object-cover"
        />
      </AspectRatio>
    </div>
  ),
};

export const SquareRatio: Story = {
  render: () => (
    <div className="w-[300px]">
      <AspectRatio ratio={1 / 1} className="bg-muted">
        <Image
          src="https://images.unsplash.com/photo-1588345921523-c2dcdb7f1dcd?w=800&dpr=2&q=80"
          alt="Photo by Drew Beamer"
          fill
          className="rounded-md object-cover"
        />
      </AspectRatio>
    </div>
  ),
};


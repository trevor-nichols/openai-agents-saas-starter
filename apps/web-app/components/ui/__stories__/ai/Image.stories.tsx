import type { Meta, StoryObj } from '@storybook/react';
import type { ImageGenerationCall } from '@/lib/api/client/types.gen';

import { Image } from '../../ai/image';

const meta: Meta<typeof Image> = {
  title: 'AI/Image',
  component: Image,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Image>;

// 1x1 png base64 (transparent)
const transparentPng =
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg==';

export const Base64: Story = {
  args: {
    base64: transparentPng,
    mediaType: 'image/png',
    alt: 'Transparent pixel',
    className: 'w-32 h-32 bg-muted',
  },
};

const square = (color: string) => {
  const encodedColor = color.startsWith('#') ? `%23${color.slice(1)}` : color;
  return `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="${encodedColor}"/></svg>`;
};

const streamingFrames: ImageGenerationCall[] = [
  {
    id: 'frame-1',
    type: 'image_generation_call',
    status: 'in_progress',
    result: square('#fcd34d'),
    format: 'svg+xml',
    revised_prompt: 'Generating draft…',
  },
  {
    id: 'frame-2',
    type: 'image_generation_call',
    status: 'partial_image',
    result: square('#60a5fa'),
    format: 'svg+xml',
    output_index: 0,
    revised_prompt: 'Adding details…',
  },
  {
    id: 'frame-3',
    type: 'image_generation_call',
    status: 'completed',
    result: square('#0ea5e9'),
    format: 'svg+xml',
    output_index: 0,
    revised_prompt: 'Final frame',
  },
];

export const StreamingFrames: Story = {
  args: {
    frames: streamingFrames,
    alt: 'Streaming image generation',
    className: 'max-w-lg',
  },
};

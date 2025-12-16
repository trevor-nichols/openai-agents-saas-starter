import type { Meta, StoryObj } from '@storybook/react';
import type { GeneratedImageFrame } from '@/lib/streams/imageFrames';

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

const streamingFrames: GeneratedImageFrame[] = [
  {
    id: 'frame-1',
    status: 'in_progress',
    src: square('#fcd34d'),
    revisedPrompt: 'Generating draft…',
  },
  {
    id: 'frame-2',
    status: 'partial_image',
    src: square('#60a5fa'),
    outputIndex: 0,
    revisedPrompt: 'Adding details…',
  },
  {
    id: 'frame-3',
    status: 'completed',
    src: square('#0ea5e9'),
    outputIndex: 0,
    revisedPrompt: 'Final frame',
  },
];

export const StreamingFrames: Story = {
  args: {
    frames: streamingFrames,
    alt: 'Streaming image generation',
    className: 'max-w-lg',
  },
};

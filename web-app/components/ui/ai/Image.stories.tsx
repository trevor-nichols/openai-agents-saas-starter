import type { Meta, StoryObj } from '@storybook/react';

import { Image } from './image';

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

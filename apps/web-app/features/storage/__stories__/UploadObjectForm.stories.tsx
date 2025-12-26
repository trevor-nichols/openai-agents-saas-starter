'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { UploadObjectForm } from '../components';

const meta: Meta<typeof UploadObjectForm> = {
  title: 'Storage/UploadObjectForm',
  component: UploadObjectForm,
  args: {
    onUploaded: () => console.log('uploaded'),
  },
};

export default meta;

type Story = StoryObj<typeof UploadObjectForm>;

export const Default: Story = {};

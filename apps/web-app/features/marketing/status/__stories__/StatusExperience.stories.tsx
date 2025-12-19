'use client';

import type { Meta, StoryObj } from '@storybook/react';
import { StatusExperience } from '../StatusExperience';

const meta: Meta<typeof StatusExperience> = {
  title: 'Marketing/Status/Page',
  component: StatusExperience,
};

export default meta;

type Story = StoryObj<typeof StatusExperience>;

export const Default: Story = {};

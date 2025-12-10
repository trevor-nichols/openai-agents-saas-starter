'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { StaticPage } from '../StaticPage';
import { staticPages } from './fixtures';

const meta: Meta<typeof StaticPage> = {
  title: 'Marketing/Static Pages/Page',
  component: StaticPage,
};

export default meta;

type Story = StoryObj<typeof StaticPage>;

export const About: Story = {
  args: {
    content: staticPages.about,
  },
};

export const Contact: Story = {
  args: {
    content: staticPages.contact,
  },
};

export const Privacy: Story = {
  args: {
    content: staticPages.privacy,
  },
};

export const Terms: Story = {
  args: {
    content: staticPages.terms,
  },
};

import type { Meta, StoryObj } from '@storybook/react';

import { AccessRequestHero } from '../components/AccessRequestHero';

const meta: Meta<typeof AccessRequestHero> = {
  title: 'Marketing/Access Request/Hero',
  component: AccessRequestHero,
};

export default meta;

type Story = StoryObj<typeof AccessRequestHero>;

export const Default: Story = {
  render: () => <AccessRequestHero />,
};

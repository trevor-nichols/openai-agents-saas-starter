import type { Meta, StoryObj } from '@storybook/react';

import { SessionsPanel } from '../components/SessionsPanel';
import { setAccountProfileState } from '@/.storybook/mocks/account-queries';

const meta: Meta<typeof SessionsPanel> = {
  title: 'Account/Sessions Panel',
  component: SessionsPanel,
};

export default meta;

type Story = StoryObj<typeof SessionsPanel>;

export const Default: Story = {
  render: () => {
    setAccountProfileState('verified');
    return <SessionsPanel />;
  },
};

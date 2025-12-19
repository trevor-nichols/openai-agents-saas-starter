import type { Meta, StoryObj } from '@storybook/react';

import { SecurityPanel } from '../components/SecurityPanel';
import { setAccountProfileState } from '@/.storybook/mocks/account-queries';

const meta: Meta<typeof SecurityPanel> = {
  title: 'Account/Security Panel',
  component: SecurityPanel,
};

export default meta;

type Story = StoryObj<typeof SecurityPanel>;

export const Default: Story = {
  render: () => {
    setAccountProfileState('default');
    return <SecurityPanel />;
  },
};

export const Verified: Story = {
  render: () => {
    setAccountProfileState('verified');
    return <SecurityPanel />;
  },
};

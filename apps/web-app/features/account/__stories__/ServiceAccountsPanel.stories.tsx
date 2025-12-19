import type { Meta, StoryObj } from '@storybook/react';

import { ServiceAccountsPanel } from '../service-accounts/ServiceAccountsPanel';
import { setAccountProfileState } from '@/.storybook/mocks/account-queries';

const meta: Meta<typeof ServiceAccountsPanel> = {
  title: 'Account/Service Accounts Panel',
  component: ServiceAccountsPanel,
};

export default meta;

type Story = StoryObj<typeof ServiceAccountsPanel>;

export const Default: Story = {
  render: () => {
    setAccountProfileState('verified');
    return <ServiceAccountsPanel />;
  },
};

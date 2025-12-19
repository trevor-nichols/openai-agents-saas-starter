import type { Meta, StoryObj } from '@storybook/react';

import { ProfilePanel } from '../components/ProfilePanel';
import { setAccountProfileState } from '@/.storybook/mocks/account-queries';

const meta: Meta<typeof ProfilePanel> = {
  title: 'Account/Profile Panel',
  component: ProfilePanel,
};

export default meta;

type Story = StoryObj<typeof ProfilePanel>;

export const Default: Story = {
  render: () => {
    setAccountProfileState('default');
    return <ProfilePanel />;
  },
};

export const VerifiedUser: Story = {
  render: () => {
    setAccountProfileState('verified');
    return <ProfilePanel />;
  },
};

export const Loading: Story = {
  render: () => {
    setAccountProfileState('loading');
    return <ProfilePanel />;
  },
};

export const ErrorState: Story = {
  render: () => {
    setAccountProfileState('error');
    return <ProfilePanel />;
  },
};

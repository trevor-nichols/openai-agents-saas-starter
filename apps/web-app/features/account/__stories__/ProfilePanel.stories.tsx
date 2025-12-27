import type { Meta, StoryObj } from '@storybook/react';

import { ProfilePanel } from '../components/ProfilePanel';
import { setAccountProfileState } from '@/.storybook/mocks/account-queries';
import { setCurrentUserProfileState } from '@/.storybook/mocks/users-queries';

const meta: Meta<typeof ProfilePanel> = {
  title: 'Account/Profile Panel',
  component: ProfilePanel,
};

export default meta;

type Story = StoryObj<typeof ProfilePanel>;

export const Default: Story = {
  render: () => {
    setAccountProfileState('default');
    setCurrentUserProfileState('default');
    return <ProfilePanel />;
  },
};

export const VerifiedUser: Story = {
  render: () => {
    setAccountProfileState('verified');
    setCurrentUserProfileState('verified');
    return <ProfilePanel />;
  },
};

export const Loading: Story = {
  render: () => {
    setAccountProfileState('loading');
    setCurrentUserProfileState('loading');
    return <ProfilePanel />;
  },
};

export const ErrorState: Story = {
  render: () => {
    setAccountProfileState('error');
    setCurrentUserProfileState('error');
    return <ProfilePanel />;
  },
};

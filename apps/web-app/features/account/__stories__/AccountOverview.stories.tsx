import type { Meta, StoryObj } from '@storybook/react';

import { AccountOverview } from '../AccountOverview';
import { setAccountProfileState } from '@/.storybook/mocks/account-queries';
import { setCurrentUserProfileState } from '@/.storybook/mocks/users-queries';

const meta: Meta<typeof AccountOverview> = {
  title: 'Account/Overview',
  component: AccountOverview,
};

export default meta;

type Story = StoryObj<typeof AccountOverview>;

export const ProfileTab: Story = {
  args: { initialTab: 'profile' },
  render: (args) => {
    setAccountProfileState('default');
    setCurrentUserProfileState('default');
    return <AccountOverview {...args} />;
  },
};

export const SecurityTab: Story = {
  args: { initialTab: 'security' },
  render: (args) => {
    setAccountProfileState('verified');
    setCurrentUserProfileState('verified');
    return <AccountOverview {...args} />;
  },
};

export const SessionsTab: Story = {
  args: { initialTab: 'sessions' },
  render: (args) => {
    setAccountProfileState('verified');
    setCurrentUserProfileState('verified');
    return <AccountOverview {...args} />;
  },
};

export const AutomationTab: Story = {
  args: { initialTab: 'automation' },
  render: (args) => {
    setAccountProfileState('verified');
    setCurrentUserProfileState('verified');
    return <AccountOverview {...args} />;
  },
};

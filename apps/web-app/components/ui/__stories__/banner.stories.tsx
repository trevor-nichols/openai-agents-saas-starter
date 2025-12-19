import type { Meta, StoryObj } from '@storybook/react';
import { Info, ShieldCheck } from 'lucide-react';

import { Banner, BannerAction, BannerClose, BannerIcon, BannerTitle } from '../banner';

const meta: Meta<typeof Banner> = {
  title: 'UI/Feedback/Banner',
  component: Banner,
  tags: ['autodocs'],
  args: {
    defaultVisible: true,
  },
};

export default meta;

type Story = StoryObj<typeof Banner>;

export const Primary: Story = {
  args: {
    children: (
      <>
        <BannerIcon icon={Info} />
        <BannerTitle>Incident resolved. Background jobs have recovered.</BannerTitle>
        <BannerAction variant="outline" size="sm">
          View Details
        </BannerAction>
        <BannerClose aria-label="Dismiss" />
      </>
    ),
  },
};

export const MutedInset: Story = {
  args: {
    inset: true,
    variant: 'muted',
    children: (
      <>
        <BannerIcon icon={ShieldCheck} />
        <BannerTitle>Security hardening enabled for new workspaces.</BannerTitle>
        <BannerAction size="sm">Learn more</BannerAction>
        <BannerClose aria-label="Dismiss" />
      </>
    ),
  },
};

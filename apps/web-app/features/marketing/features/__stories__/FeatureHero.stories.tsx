'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { FeatureHero } from '../components/FeatureHero';
import { FEATURES_CTA } from '../constants';
import { FEATURE_NAV } from '../constants';

const meta: Meta<typeof FeatureHero> = {
  title: 'Marketing/Features/Hero',
  component: FeatureHero,
  args: {
    eyebrow: 'Features',
    title: 'Enterprise-grade building blocks',
    description: 'Ship agents, billing, and ops faster.',
    primaryCta: FEATURES_CTA.primaryCta,
    secondaryCta: FEATURES_CTA.secondaryCta,
    navItems: FEATURE_NAV,
    onCtaClick: () => console.log('cta click'),
  },
};

export default meta;

type Story = StoryObj<typeof FeatureHero>;

export const Default: Story = {};

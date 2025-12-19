'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { PricingHero } from '../components/PricingHero';
import { PRICING_HERO_COPY } from '../constants';

const meta: Meta<typeof PricingHero> = {
  title: 'Marketing/Pricing/Hero',
  component: PricingHero,
  args: {
    eyebrow: PRICING_HERO_COPY.eyebrow,
    title: PRICING_HERO_COPY.title,
    description: PRICING_HERO_COPY.description,
    primaryCta: PRICING_HERO_COPY.primaryCta,
    secondaryCta: PRICING_HERO_COPY.secondaryCta,
    onCtaClick: (meta) => console.log('CTA click', meta),
  },
};

export default meta;

type Story = StoryObj<typeof PricingHero>;

export const Default: Story = {};

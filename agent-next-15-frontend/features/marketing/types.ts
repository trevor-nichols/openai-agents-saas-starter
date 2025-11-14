export type CtaIntent = 'primary' | 'secondary';

export interface CtaLink {
  label: string;
  href: string;
  intent: CtaIntent;
}

export interface CtaConfig {
  title: string;
  description: string;
  eyebrow?: string;
  primaryCta: CtaLink;
  secondaryCta: CtaLink;
}

export interface MarketingFaqItem {
  question: string;
  answer: string;
}

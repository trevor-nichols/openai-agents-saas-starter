import type { ReactNode } from 'react';

export type StaticSection = {
  title: string;
  body: string;
  bullets?: string[];
  aside?: ReactNode;
};

export type StaticPageContent = {
  eyebrow: string;
  title: string;
  description: string;
  updated?: string;
  sections: StaticSection[];
};

export const ABOUT_PAGE: StaticPageContent = {
  eyebrow: 'Company',
  title: 'Built for teams shipping AI agents to production',
  description:
    'We created this starter so product, platform, and security teams can launch GPT-5 agent consoles without rebuilding auth, billing, and observability.',
  sections: [
    {
      title: 'What we ship',
      body: 'A production-ready FastAPI + Next.js 16 stack with the OpenAI Agents SDK v0.6.1, Ed25519 JWT auth, billing rails, and ops telemetry already wired.',
      bullets: [
        'Opinionated feature directories for marketing, workspace, billing, and status',
        'Starter CLI for env hydration, keys, and audit exports',
        'Stripe-ready metering plus provider-agnostic interfaces',
      ],
    },
    {
      title: 'Why this exists',
      body: 'Most teams lose weeks re-implementing the same scaffolding. This repo lets you focus on your agent workflows and UI while keeping enterprise controls intact.',
    },
    {
      title: 'Who we are',
      body: 'Built by a small crew of AI infra engineers who have shipped agent copilots at scale. Swap this section with your founders, mission, and proof points when you clone the starter.',
      bullets: [
        'Add a one-liner about your team (e.g., ex-FAANG, ex-startups)',
        'Name your core differentiators in two bullets',
        'Link to your security/architecture one-pager',
      ],
    },
  ],
};

export const CONTACT_PAGE: StaticPageContent = {
  eyebrow: 'Contact',
  title: 'Talk to the team',
  description: 'Need help wiring the starter, running a security review, or extending the Agents SDK? Reach out and we will respond within one business day.',
  sections: [
    {
      title: 'Support channels',
      body: 'Pick the path that matches your request. We triage weekday hours (9–5 PT).',
      bullets: [
        'Email: support@yourcompany.com',
        'Security: security@yourcompany.com',
        'Partnerships: partners@yourcompany.com',
      ],
    },
    {
      title: 'What to include',
      body: 'To speed up responses, share your repo link, deployment target, and which surfaces you are modifying (agents, billing, marketing, or CLI).',
    },
  ],
};

export const PRIVACY_PAGE: StaticPageContent = {
  eyebrow: 'Privacy',
  title: 'Privacy & data handling',
  description: 'We minimize data collection and keep telemetry scoped to operating the starter and improving the open-source project.',
  updated: 'November 30, 2025',
  sections: [
    {
      title: 'Data we collect',
      body: 'If you register on the hosted demo we store your account info, workspace settings, and usage needed for billing analytics. Self-hosted deployments keep data in your infra.',
      bullets: [
        'Account: email, name, org for auth',
        'Usage: plan + metering records for billing surfaces',
        'Telemetry: anonymized performance metrics for reliability',
      ],
    },
    {
      title: 'Your controls',
      body: 'Request export or deletion at any time via security@example.com. Self-hosted operators manage their own retention and logging policies.',
    },
    {
      title: 'Processors',
      body: 'Stripe for payments, Sentry for error monitoring, and hosting on your chosen cloud. We do not sell or share data with advertisers.',
    },
  ],
};

export const TERMS_PAGE: StaticPageContent = {
  eyebrow: 'Terms',
  title: 'Terms of use',
  description: 'Use of the hosted demo and starter codebase is governed by these terms. For commercial support or custom licensing, contact partners@example.com.',
  updated: 'November 30, 2025',
  sections: [
    {
      title: 'Acceptable use',
      body: 'No abuse, fraud, or attempts to attack the platform. Do not upload sensitive production data to the hosted demo.',
    },
    {
      title: 'Warranty',
      body: 'The starter is provided as-is without warranties. You are responsible for securing your deployments and reviewing dependencies.',
    },
    {
      title: 'Limitation of liability',
      body: 'To the maximum extent permitted by law, liability is limited to the amount you paid for hosted services, if any.',
    },
    {
      title: 'Open-source license',
      body: 'See LICENSE in the repo for full text. Contributions are welcomed under the contributor agreement.',
    },
  ],
};

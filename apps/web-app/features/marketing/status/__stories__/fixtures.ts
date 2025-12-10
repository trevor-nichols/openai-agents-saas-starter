import type { PlatformStatusSnapshot } from '@/types/status';
import type { SubscriptionBanner } from '../utils/statusFormatting';

export const mockStatus: PlatformStatusSnapshot = {
  generatedAt: '2024-12-10T12:00:00Z',
  overview: {
    state: 'operational',
    description: 'All systems operational. Next.js frontend and FastAPI backend are healthy.',
    updatedAt: '2024-12-10T11:58:00Z',
  },
  services: [
    {
      name: 'Frontend',
      status: 'operational',
      description: 'Next.js app router and CDN edge.',
      owner: 'web-platform',
      lastIncidentAt: '2024-12-01T12:00:00Z',
    },
    {
      name: 'API',
      status: 'degraded_performance',
      description: 'FastAPI and background workers.',
      owner: 'api-platform',
      lastIncidentAt: '2024-12-08T09:00:00Z',
    },
    {
      name: 'Billing',
      status: 'operational',
      description: 'Stripe webhooks and invoicing',
      owner: 'finops',
      lastIncidentAt: null,
    },
  ],
  incidents: [
    {
      id: 'inc-1',
      service: 'API',
      occurredAt: '2024-12-08T09:00:00Z',
      impact: 'intermittent 502s',
      state: 'resolved',
    },
    {
      id: 'inc-2',
      service: 'Billing',
      occurredAt: '2024-12-05T14:30:00Z',
      impact: 'delayed invoice emails',
      state: 'monitoring',
    },
  ],
  uptimeMetrics: [
    { label: 'Frontend uptime', value: '99.95%', helperText: '30d rolling', trendValue: '+0.02%', trendTone: 'positive' },
    { label: 'API uptime', value: '99.80%', helperText: '30d rolling', trendValue: '-0.05%', trendTone: 'negative' },
    { label: 'Billing events', value: '99.90%', helperText: 'Stripe webhooks', trendValue: '±0.00%', trendTone: 'neutral' },
  ],
};

export const mockBanner: SubscriptionBanner = {
  tone: 'warning',
  title: 'Verification pending',
  description: 'Check your inbox to confirm status alerts for prod.',
};

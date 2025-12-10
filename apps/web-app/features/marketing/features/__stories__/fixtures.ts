import type { MetricsSummary } from '../types';

export const mockMetrics: MetricsSummary[] = [
  { label: 'Agents ready', value: '5+', helperText: 'Configured via Agents SDK.' },
  { label: 'Tools wired', value: '8 tools', helperText: 'Registry scoped per agent.' },
  { label: 'Plan catalog', value: '3 tiers', helperText: 'Usage + seat pricing.' },
  { label: 'Uptime', value: '99.95%', helperText: 'Rolling 30 days.' },
];

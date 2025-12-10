import type { BillingContact, TenantSettings } from '@/types/tenantSettings';

const now = Date.now();

export const sampleContacts: BillingContact[] = [
  {
    id: 'contact-1',
    name: 'Ava Patel',
    email: 'ava@acme.com',
    role: 'Finance lead',
    phone: '+1 415 555 0101',
    notifyBilling: true,
  },
  {
    id: 'contact-2',
    name: 'Jordan Lee',
    email: 'jordan@acme.com',
    role: 'Ops',
    phone: null,
    notifyBilling: false,
  },
];

export const sampleTenantSettings: TenantSettings = {
  tenantId: 'tenant-story',
  billingContacts: sampleContacts,
  billingWebhookUrl: 'https://hooks.example.com/billing',
  planMetadata: {
    plan: 'enterprise',
    seats: '25',
    region: 'us-west',
  },
  flags: {
    usage_alerts: true,
    advanced_audit: false,
    workflows_beta: true,
  },
  updatedAt: new Date(now - 60 * 60 * 1000).toISOString(),
};

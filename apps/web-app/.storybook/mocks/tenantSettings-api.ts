import type { TenantSettings, TenantSettingsUpdateInput } from '@/types/tenantSettings';

let settings: TenantSettings = {
  tenantId: 'tenant-123',
  billingContacts: [
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
  ],
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
  updatedAt: new Date().toISOString(),
};

export async function fetchTenantSettings(): Promise<TenantSettings> {
  return settings;
}

export async function updateTenantSettings(patch: Partial<TenantSettingsUpdateInput>): Promise<TenantSettings> {
  settings = {
    ...settings,
    billingContacts: patch.billingContacts ?? settings.billingContacts,
    billingWebhookUrl:
      patch.billingWebhookUrl !== undefined ? patch.billingWebhookUrl : settings.billingWebhookUrl,
    planMetadata: patch.planMetadata ?? settings.planMetadata,
    flags: patch.flags ?? settings.flags,
    updatedAt: new Date().toISOString(),
  };
  return settings;
}

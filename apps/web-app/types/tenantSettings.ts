export interface BillingContact {
  id: string;
  name: string;
  email: string;
  role: string | null;
  phone: string | null;
  notifyBilling: boolean;
}

export const RESERVED_TENANT_FLAG_PREFIX = 'feature.';

export interface TenantSettings {
  tenantId: string;
  billingContacts: BillingContact[];
  billingWebhookUrl: string | null;
  planMetadata: Record<string, string>;
  flags: Record<string, boolean>;
  version: number;
  updatedAt: string | null;
}

export interface TenantSettingsUpdateInput {
  billingContacts: BillingContact[];
  billingWebhookUrl: string | null;
  planMetadata: Record<string, string>;
  flags: Record<string, boolean>;
}

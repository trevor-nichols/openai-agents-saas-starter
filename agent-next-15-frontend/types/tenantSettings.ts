export interface BillingContactDto {
  name: string;
  email: string;
  role?: string | null;
  phone?: string | null;
  notify_billing?: boolean;
}

export interface TenantSettingsResponseDto {
  tenant_id: string;
  billing_contacts: BillingContactDto[];
  billing_webhook_url: string | null;
  plan_metadata: Record<string, string>;
  flags: Record<string, boolean>;
  updated_at: string | null;
}

export interface TenantSettingsUpdateDto {
  billing_contacts: BillingContactDto[];
  billing_webhook_url: string | null;
  plan_metadata: Record<string, string>;
  flags: Record<string, boolean>;
}

export interface BillingContact {
  id: string;
  name: string;
  email: string;
  role: string | null;
  phone: string | null;
  notifyBilling: boolean;
}

export interface TenantSettings {
  tenantId: string;
  billingContacts: BillingContact[];
  billingWebhookUrl: string | null;
  planMetadata: Record<string, string>;
  flags: Record<string, boolean>;
  updatedAt: string | null;
}

export interface TenantSettingsUpdateInput {
  billingContacts: BillingContact[];
  billingWebhookUrl: string | null;
  planMetadata: Record<string, string>;
  flags: Record<string, boolean>;
}

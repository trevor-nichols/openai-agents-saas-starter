import type {
  BillingContact,
  BillingContactDto,
  TenantSettings,
  TenantSettingsResponseDto,
  TenantSettingsUpdateDto,
  TenantSettingsUpdateInput,
} from '@/types/tenantSettings';

function mapContact(dto: BillingContactDto, index: number): BillingContact {
  const idSeat = dto.email ? `${dto.email}:${index}` : `contact-${index}`;
  return {
    id: idSeat,
    name: dto.name,
    email: dto.email,
    role: dto.role ?? null,
    phone: dto.phone ?? null,
    notifyBilling: dto.notify_billing ?? true,
  };
}

function mapDto(dto: TenantSettingsResponseDto): TenantSettings {
  return {
    tenantId: dto.tenant_id,
    billingContacts: dto.billing_contacts.map(mapContact),
    billingWebhookUrl: dto.billing_webhook_url,
    planMetadata: dto.plan_metadata ?? {},
    flags: dto.flags ?? {},
    updatedAt: dto.updated_at,
  };
}

function mapContactToDto(contact: BillingContact): BillingContactDto {
  return {
    name: contact.name,
    email: contact.email,
    role: contact.role ?? undefined,
    phone: contact.phone ?? undefined,
    notify_billing: contact.notifyBilling,
  };
}

function buildUpdateDto(payload: TenantSettingsUpdateInput): TenantSettingsUpdateDto {
  return {
    billing_contacts: payload.billingContacts.map(mapContactToDto),
    billing_webhook_url: payload.billingWebhookUrl,
    plan_metadata: payload.planMetadata,
    flags: payload.flags,
  };
}

function createError(response: Response, fallbackMessage: string, detail?: string): Error {
  const base = detail || (response.status === 401 ? 'You have been signed out. Please log back in.' : fallbackMessage);
  return new Error(base);
}

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch (_error) {
    throw new Error('Failed to parse API response.');
  }
}

function extractErrorMessage(payload: unknown): string | undefined {
  if (!payload || typeof payload !== 'object') {
    return undefined;
  }
  const record = payload as Record<string, unknown>;
  const detail = record.message ?? record.detail;
  return typeof detail === 'string' ? detail : undefined;
}

export async function fetchTenantSettings(): Promise<TenantSettings> {
  const response = await fetch('/api/settings/tenant', { cache: 'no-store' });
  const payload = await parseJson<unknown>(response);
  if (!response.ok) {
    throw createError(
      response,
      'Unable to load tenant settings.',
      extractErrorMessage(payload),
    );
  }
  return mapDto(payload as TenantSettingsResponseDto);
}

export async function updateTenantSettings(
  payload: TenantSettingsUpdateInput,
): Promise<TenantSettings> {
  const response = await fetch('/api/settings/tenant', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(buildUpdateDto(payload)),
  });
  const body = await parseJson<unknown>(response);
  if (!response.ok) {
    throw createError(
      response,
      'Unable to update tenant settings.',
      extractErrorMessage(body),
    );
  }
  return mapDto(body as TenantSettingsResponseDto);
}

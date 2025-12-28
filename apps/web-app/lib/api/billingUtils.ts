export type BillingErrorPayload = {
  message?: string;
  error?: string;
};

interface BillingHeaderOptions {
  tenantRole?: string | null;
}

function resolvePayloadMessage(payload: unknown): string | null {
  if (!payload || typeof payload !== 'object') {
    return null;
  }
  const candidate = payload as BillingErrorPayload;
  if (candidate.message && typeof candidate.message === 'string') {
    return candidate.message;
  }
  if (candidate.error && typeof candidate.error === 'string') {
    return candidate.error;
  }
  return null;
}

export function buildBillingHeaders(
  options?: BillingHeaderOptions,
  includeJson: boolean = false,
): HeadersInit {
  const headers: Record<string, string> = {};
  if (includeJson) {
    headers['Content-Type'] = 'application/json';
  }
  if (options?.tenantRole) {
    headers['X-Tenant-Role'] = options.tenantRole;
  }
  return headers;
}

export function isBillingDisabled(status: number, payload: unknown): boolean {
  if (status !== 404) {
    return false;
  }
  const message = resolvePayloadMessage(payload);
  if (!message) {
    return false;
  }
  return message.toLowerCase().includes('billing is disabled');
}

export function resolveBillingErrorMessage(payload: unknown, fallbackMessage: string): string {
  const message = resolvePayloadMessage(payload);
  return message ?? fallbackMessage;
}

export async function parseBillingResponse<T>(response: Response): Promise<T | BillingErrorPayload> {
  try {
    return (await response.json()) as T;
  } catch (_error) {
    return {};
  }
}

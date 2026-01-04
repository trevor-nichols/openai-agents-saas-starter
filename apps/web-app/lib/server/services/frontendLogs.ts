import 'server-only';

import { createHmac } from 'node:crypto';

import { jsonBodySerializer } from '@/lib/api/client/core/bodySerializer.gen';
import { ingestFrontendLogApiV1LogsPost } from '@/lib/api/client/sdk.gen';
import type { FrontendLogPayload } from '@/lib/api/client/types.gen';
import { ACCESS_TOKEN_COOKIE } from '@/lib/config';
import { createApiClient } from '../apiClient';

export interface FrontendLogForwardOptions {
  payload: FrontendLogPayload;
  authorization?: string | null;
  cookie?: string | null;
}

export interface FrontendLogForwardResult {
  status: number;
  ok: boolean;
  body: unknown | null;
  retryAfter?: string | null;
}

function getCookieValue(cookieHeader: string, name: string): string | null {
  const parts = cookieHeader.split(';');
  for (const part of parts) {
    const [key, ...rest] = part.trim().split('=');
    if (!key) continue;
    if (key === name) {
      return rest.join('=') || null;
    }
  }
  return null;
}

function signBody(body: string): string | null {
  const secret = process.env.FRONTEND_LOG_SHARED_SECRET;
  if (!secret) return null;
  return createHmac('sha256', secret).update(body).digest('hex');
}

function resolveTextPayload(error: unknown): string {
  if (!error) return '';
  if (typeof error === 'string') return error;
  try {
    return JSON.stringify(error);
  } catch {
    return '';
  }
}

export async function forwardFrontendLog(
  options: FrontendLogForwardOptions,
): Promise<FrontendLogForwardResult> {
  const serializedBody = jsonBodySerializer.bodySerializer(options.payload);
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };

  if (options.authorization) {
    headers.Authorization = options.authorization;
  } else if (options.cookie) {
    const accessToken = getCookieValue(options.cookie, ACCESS_TOKEN_COOKIE);
    if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  }

  if (!headers.Authorization) {
    const signature = signBody(serializedBody);
    if (signature) headers['X-Log-Signature'] = signature;
  }

  const client = createApiClient();
  const response = await ingestFrontendLogApiV1LogsPost({
    client,
    throwOnError: false,
    responseStyle: 'fields',
    parseAs: 'text',
    headers,
    body: options.payload,
    bodySerializer: () => serializedBody,
    cache: 'no-store',
    redirect: 'manual',
  });

  const raw = response.data;
  const text = typeof raw === 'string'
    ? raw
    : resolveTextPayload('error' in response ? response.error : raw);
  let parsed: unknown = null;
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = { message: text };
    }
  }

  return {
    status: response.response?.status ?? 502,
    ok: response.response?.ok ?? false,
    body: parsed,
    retryAfter: response.response?.headers.get('retry-after') ?? null,
  };
}

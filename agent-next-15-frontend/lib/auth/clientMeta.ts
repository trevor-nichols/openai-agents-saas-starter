'use client';

import { SESSION_META_COOKIE } from '../config';

export type ClientSessionMeta = {
  tenantId: string;
  userId: string;
  expiresAt: string;
  scopes: string[];
};

function decodeBase64Url(value: string): string {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized.padEnd(normalized.length + (4 - (normalized.length % 4)) % 4, '=');
  if (typeof window === 'undefined') {
    return Buffer.from(padded, 'base64').toString('utf-8');
  }
  return window.atob(padded);
}

export function readClientSessionMeta(): ClientSessionMeta | null {
  if (typeof document === 'undefined') {
    return null;
  }
  const entry = document.cookie
    .split(';')
    .map((chunk) => chunk.trim())
    .find((chunk) => chunk.startsWith(`${SESSION_META_COOKIE}=`));
  if (!entry) {
    return null;
  }
  const value = entry.split('=').slice(1).join('=');
  try {
    const decoded = decodeBase64Url(value);
    const parsed = JSON.parse(decoded);
    return {
      tenantId: parsed.tenantId,
      userId: parsed.userId,
      expiresAt: parsed.expiresAt,
      scopes: parsed.scopes ?? [],
    };
  } catch (error) {
    console.warn('[billing] Failed to parse session meta cookie', error);
    return null;
  }
}

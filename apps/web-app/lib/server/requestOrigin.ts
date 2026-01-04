'use server';

import { headers } from 'next/headers';

import { getSiteUrl } from '@/lib/seo/siteUrl';

const stripTrailingSlash = (value: string) => (value.endsWith('/') ? value.slice(0, -1) : value);

function firstForwardedHeader(value: string | null): string | null {
  if (!value) return null;
  const [first] = value.split(',');
  const trimmed = first?.trim();
  return trimmed ? trimmed : null;
}

function hostWithoutPort(host: string): string {
  const trimmed = host.trim();
  if (!trimmed) return trimmed;
  if (trimmed.startsWith('[')) {
    const end = trimmed.indexOf(']');
    if (end > 0) {
      return trimmed.slice(1, end);
    }
  }
  const colonCount = (trimmed.match(/:/g) ?? []).length;
  if (colonCount > 1) {
    return trimmed;
  }
  return trimmed.split(':')[0] ?? trimmed;
}

function isLocalHost(host: string): boolean {
  const normalized = hostWithoutPort(host).toLowerCase();
  if (normalized === 'localhost' || normalized === '::1' || normalized === '0.0.0.0') {
    return true;
  }
  if (normalized.startsWith('127.')) {
    return true;
  }
  return normalized.endsWith('.local');
}

export async function getRequestOrigin(): Promise<string> {
  try {
    const headerList = await headers();
    const host = firstForwardedHeader(headerList.get('x-forwarded-host'))
      ?? firstForwardedHeader(headerList.get('host'));

    if (host) {
      const proto =
        firstForwardedHeader(headerList.get('x-forwarded-proto'))
        ?? (isLocalHost(host) ? 'http' : 'https');
      return stripTrailingSlash(`${proto}://${host}`);
    }
  } catch {
    // Fall through to APP_PUBLIC_URL when request headers are unavailable.
  }

  return getSiteUrl();
}

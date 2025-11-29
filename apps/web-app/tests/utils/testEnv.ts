import path from 'node:path';

const truthy = new Set(['1', 'true', 'yes']);

export function getApiBaseUrl(): string {
  const raw = process.env.PLAYWRIGHT_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  return raw.replace(/\/+$/, '');
}

export function isPublicSignupEnabled(): boolean {
  const raw =
    process.env.PLAYWRIGHT_ALLOW_PUBLIC_SIGNUP ||
    process.env.ALLOW_PUBLIC_SIGNUP ||
    process.env.NEXT_PUBLIC_ALLOW_PUBLIC_SIGNUP;
  if (!raw) {
    return false;
  }
  return truthy.has(raw.trim().toLowerCase());
}

export function getFixturesPath(): string {
  return path.resolve(__dirname, '..', '.fixtures.json');
}

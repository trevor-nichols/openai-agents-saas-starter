const FALLBACK_SITE_URL = 'http://localhost:3000';

const stripTrailingSlash = (value: string) => (value.endsWith('/') ? value.slice(0, -1) : value);

export function getSiteUrl(): string {
  const raw =
    process.env.SITE_URL ||
    process.env.NEXT_PUBLIC_SITE_URL ||
    process.env.NEXT_PUBLIC_VERCEL_URL && `https://${process.env.NEXT_PUBLIC_VERCEL_URL}` ||
    FALLBACK_SITE_URL;

  let parsed: URL;
  try {
    parsed = new URL(raw);
  } catch {
    throw new Error(`Invalid SITE_URL provided: ${raw}`);
  }

  if (parsed.pathname && parsed.pathname !== '/' && parsed.pathname !== '') {
    throw new Error('SITE_URL must not include a path; provide protocol + host (+ optional port) only');
  }

  const protocol = parsed.protocol.toLowerCase();
  if (protocol !== 'http:' && protocol !== 'https:') {
    throw new Error('SITE_URL must use http or https');
  }

  const host = parsed.hostname.toLowerCase();
  const port = parsed.port ? `:${parsed.port}` : '';

  return stripTrailingSlash(`${protocol}//${host}${port}`);
}

export function buildAbsoluteUrl(path: string): string {
  const base = getSiteUrl();
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${normalizedPath}`;
}

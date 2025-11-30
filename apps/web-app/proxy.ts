import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

import { ACCESS_TOKEN_COOKIE } from '@/lib/config';

const PUBLIC_EXACT_PATHS = new Set([
  '/',
  '/pricing',
  '/features',
  '/docs',
  '/login',
  '/register',
  '/request-access',
  '/contact',
  '/about',
  '/terms',
  '/privacy',
  '/status',
]);
const PUBLIC_PREFIXES = ['/password', '/email', '/api', '/_next', '/favicon.ico'];
const AUTH_EXACT_PATHS = new Set(['/login', '/register']);
const AUTH_PREFIXES = ['/password', '/email'];

export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  const isPublic =
    PUBLIC_EXACT_PATHS.has(pathname) || PUBLIC_PREFIXES.some((prefix) => pathname.startsWith(prefix));
  const isAuthRoute =
    AUTH_EXACT_PATHS.has(pathname) || AUTH_PREFIXES.some((prefix) => pathname.startsWith(prefix));
  const hasSession = Boolean(request.cookies.get(ACCESS_TOKEN_COOKIE)?.value);

  if (!hasSession && !isPublic) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = '/login';
    const intendedPath = `${pathname}${search}` || '/dashboard';
    loginUrl.searchParams.set('redirectTo', intendedPath);
    return NextResponse.redirect(loginUrl);
  }

  if (hasSession && isAuthRoute) {
    const homeUrl = request.nextUrl.clone();
    homeUrl.pathname = '/dashboard';
    return NextResponse.redirect(homeUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};

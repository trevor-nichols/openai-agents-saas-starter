import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

import { ACCESS_TOKEN_COOKIE } from '@/lib/config';

const PUBLIC_EXACT_PATHS = new Set(['/', '/pricing', '/features', '/docs', '/login', '/register']);
const PUBLIC_PREFIXES = ['/password', '/email', '/api', '/_next', '/favicon.ico'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const isPublic =
    PUBLIC_EXACT_PATHS.has(pathname) || PUBLIC_PREFIXES.some((prefix) => pathname.startsWith(prefix));
  const hasSession = Boolean(request.cookies.get(ACCESS_TOKEN_COOKIE)?.value);

  if (!hasSession && !isPublic) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = '/login';
    loginUrl.searchParams.set('redirectTo', pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (hasSession && (pathname === '/login' || pathname === '/register')) {
    const homeUrl = request.nextUrl.clone();
    homeUrl.pathname = '/dashboard';
    return NextResponse.redirect(homeUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};

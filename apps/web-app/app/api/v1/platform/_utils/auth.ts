import { NextResponse } from 'next/server';

import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { hasOperatorScope } from '@/lib/auth/roles';

export type OperatorSession = {
  userId: string;
  tenantId: string;
  scopes: string[];
  expiresAt: string;
  refreshExpiresAt: string;
};

export async function requireOperatorSession(): Promise<
  | { ok: true; session: OperatorSession }
  | { ok: false; response: NextResponse }
> {
  const session = await getSessionMetaFromCookies();
  if (!session) {
    return {
      ok: false,
      response: NextResponse.json({ success: false, error: 'Missing access token.' }, { status: 401 }),
    };
  }
  if (!hasOperatorScope(session.scopes)) {
    return {
      ok: false,
      response: NextResponse.json(
        { success: false, error: 'Forbidden: operator scope required.' },
        { status: 403 },
      ),
    };
  }
  return { ok: true, session };
}

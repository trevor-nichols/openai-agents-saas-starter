import { NextRequest, NextResponse } from 'next/server';

import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { adminResetPassword } from '@/lib/server/services/auth/passwords';
import { z } from 'zod';

const SUPPORT_SCOPE = 'support:read';

const payloadSchema = z.object({
  user_id: z.string().trim().min(1, 'user_id is required.'),
  new_password: z.string().trim().min(14, 'new_password must be at least 14 characters.'),
});

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();

  if (normalized.includes('missing access token')) return 401;
  if (normalized.includes('support:read') || normalized.includes('forbidden')) return 403;
  if (normalized.includes('tenant context') || normalized.includes('invalid tenant')) return 400;
  if (normalized.includes('policy') || normalized.includes('reuse')) return 400;
  if (normalized.includes('password reset returned empty response')) return 500;
  if (normalized.includes('validation') || normalized.includes('unprocessable') || normalized.includes('payload')) return 422;
  if (normalized.includes('invalid access token') || normalized.includes('invalid refresh token')) return 401;
  if (normalized.includes('not found')) return 404;
  if (normalized.includes('rate limit')) return 429;
  return 500;
}

export async function POST(request: NextRequest) {
  const session = await getSessionMetaFromCookies();

  if (!session) {
    return NextResponse.json({ message: 'Missing access token.' }, { status: 401 });
  }

  if (!session.scopes?.includes(SUPPORT_SCOPE)) {
    return NextResponse.json({ message: 'Forbidden: support:read scope required.' }, { status: 403 });
  }

  if (!session.tenantId) {
    return NextResponse.json(
      { message: 'Tenant context is required for password reset.' },
      { status: 400 },
    );
  }

  try {
    const json = await request.json();
    const payload = payloadSchema.parse(json);
    const response = await adminResetPassword(payload);
    return NextResponse.json(response, { status: 200 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { message: 'Invalid payload.', issues: error.flatten() },
        { status: 422 },
      );
    }
    const message = error instanceof Error ? error.message : String(error);
    const normalizedMessage = message.toLowerCase();
    if (normalizedMessage.includes('password reset returned empty response')) {
      return NextResponse.json({ message }, { status: 500 });
    }
    const status = mapErrorToStatus(message);
    if (status === 422) {
      return NextResponse.json({ message: 'Invalid payload.', issues: {} }, { status });
    }
    return NextResponse.json({ message }, { status });
  }
}

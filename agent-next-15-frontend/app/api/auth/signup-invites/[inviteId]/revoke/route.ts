import { NextResponse } from 'next/server';

import { normalizeSignupGuardrailError } from '@/app/api/auth/_utils/signupGuardrailResponses';
import { revokeSignupInvite } from '@/lib/server/services/auth/signupGuardrails';

interface RouteParams {
  params: {
    inviteId?: string;
  };
}

export async function POST(_request: Request, { params }: RouteParams) {
  const inviteId = params?.inviteId;
  if (!inviteId) {
    return NextResponse.json(
      {
        success: false,
        error: 'Invite id is required.',
      },
      { status: 400 },
    );
  }

  try {
    const invite = await revokeSignupInvite(inviteId);
    return NextResponse.json(
      {
        success: true,
        data: invite,
      },
      { status: 200 },
    );
  } catch (error) {
    const normalized = normalizeSignupGuardrailError(error, 'Unable to revoke signup invite.');
    return NextResponse.json(
      {
        success: false,
        error: normalized.message,
      },
      { status: normalized.status },
    );
  }
}

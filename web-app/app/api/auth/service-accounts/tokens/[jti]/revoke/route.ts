import { NextRequest, NextResponse } from 'next/server';

import { revokeServiceAccountToken } from '@/lib/server/services/auth/serviceAccounts';

type RouteParams = {
  params: Promise<{
    jti: string;
  }>;
};

export async function POST(request: NextRequest, { params }: RouteParams) {
  const { jti: tokenId } = await params;
  if (!tokenId) {
    return NextResponse.json(
      {
        success: false,
        error: 'Token id is required.',
      },
      { status: 400 },
    );
  }

  const reason = await extractReason(request);

  try {
    await revokeServiceAccountToken(tokenId, reason);
    return NextResponse.json(
      {
        success: true,
        data: {
          jti: tokenId,
        },
      },
      { status: 200 },
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to revoke service-account token.';
    const status = mapErrorToStatus(message);
    return NextResponse.json(
      {
        success: false,
        error: message,
      },
      { status },
    );
  }
}

async function extractReason(request: NextRequest): Promise<string | undefined> {
  try {
    const payload = (await request.json()) as { reason?: string | null };
    if (payload?.reason && typeof payload.reason === 'string') {
      const trimmed = payload.reason.trim();
      return trimmed.length > 0 ? trimmed : undefined;
    }
  } catch (_error) {
    // ignore body parse issues and treat as undefined reason
  }
  return undefined;
}

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  if (normalized.includes('forbidden')) {
    return 403;
  }
  if (normalized.includes('not found')) {
    return 404;
  }
  return 500;
}

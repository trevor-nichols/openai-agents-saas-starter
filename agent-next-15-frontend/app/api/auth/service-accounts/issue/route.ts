import { NextRequest, NextResponse } from 'next/server';

import { issueServiceAccountToken } from '@/lib/server/services/auth/serviceAccounts';

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  if (normalized.includes('invalid')) {
    return 400;
  }
  return 500;
}

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json();
    const token = await issueServiceAccountToken(payload, {
      vaultPayload: request.headers.get('x-vault-payload'),
    });
    return NextResponse.json(token, { status: 201 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to issue service account token.';
    const status = mapErrorToStatus(message);
    return NextResponse.json({ message }, { status });
  }
}


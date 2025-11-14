import { NextRequest, NextResponse } from 'next/server';

import { issueVaultServiceAccountToken } from '@/lib/server/services/auth/serviceAccounts';

export async function POST(request: NextRequest) {
  const authorization = request.headers.get('x-vault-authorization');
  const vaultPayload = request.headers.get('x-vault-payload');

  if (!authorization) {
    return NextResponse.json(
      {
        success: false,
        error: 'X-Vault-Authorization header is required.',
      },
      { status: 400 },
    );
  }

  const body = await request.json();

  try {
    const result = await issueVaultServiceAccountToken({
      mode: 'vault',
      account: body.account,
      scopes: body.scopes,
      tenantId: body.tenant_id ?? null,
      lifetimeMinutes: body.lifetime_minutes ?? undefined,
      fingerprint: body.fingerprint ?? undefined,
      force: Boolean(body.force),
      reason: body.reason ?? '',
      vaultAuthorization: authorization,
      vaultPayload: vaultPayload ?? null,
    });

    return NextResponse.json(
      {
        success: true,
        data: result,
      },
      { status: 201 },
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to issue service-account token.';
    const statusCode = mapErrorToStatus(message);
    return NextResponse.json(
      {
        success: false,
        error: message,
      },
      { status: statusCode },
    );
  }
}

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  if (normalized.includes('forbidden')) {
    return 403;
  }
  if (normalized.includes('vault authorization')) {
    return 400;
  }
  if (normalized.includes('rate limit')) {
    return 429;
  }
  return 502;
}

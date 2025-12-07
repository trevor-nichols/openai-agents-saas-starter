import { NextResponse } from 'next/server';

import { revokeMfaMethodApiV1AuthMfaMethodIdDelete } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

interface RouteContext {
  params: Promise<{
    methodId: string;
  }>;
}

export async function DELETE(_request: Request, context: RouteContext) {
  const { methodId } = await context.params;
  if (!methodId) {
    return NextResponse.json({ message: 'methodId is required.' }, { status: 400 });
  }
  try {
    const { client, auth } = await getServerApiClient();
    await revokeMfaMethodApiV1AuthMfaMethodIdDelete({
      client,
      auth,
      throwOnError: true,
      path: { method_id: methodId },
    });
    return NextResponse.json({ message: 'MFA method revoked.' });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to revoke MFA method.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 400;
    return NextResponse.json({ message }, { status });
  }
}

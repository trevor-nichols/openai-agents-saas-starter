import { NextResponse } from 'next/server';

import { revokeMfaMethod } from '@/lib/server/services/auth/mfa';

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
    await revokeMfaMethod(methodId);
    return NextResponse.json({ message: 'MFA method revoked.' });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to revoke MFA method.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 400;
    return NextResponse.json({ message }, { status });
  }
}

import { NextResponse } from 'next/server';

import type { UserLoginRequest } from '@/lib/api/client/types.gen';
import { exchangeCredentials } from '@/lib/auth/session';

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as UserLoginRequest;
    if (!payload?.email || !payload?.password) {
      return NextResponse.json({ message: 'email and password are required' }, { status: 400 });
    }

    const tokens = await exchangeCredentials({
      email: payload.email,
      password: payload.password,
      tenant_id: payload.tenant_id ?? null,
    });

    return NextResponse.json(tokens, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to log in.';
    const status = message.toLowerCase().includes('invalid') ? 401 : 502;
    return NextResponse.json({ message }, { status });
  }
}

import { NextRequest, NextResponse } from 'next/server';

import { issueEmailVerificationToken } from '@/lib/server/services/testFixtures';

export async function POST(req: NextRequest) {
  if (process.env.NODE_ENV === 'production') {
    return NextResponse.json({ error: 'Not found' }, { status: 404 });
  }

  const body = await req.text();
  const response = await issueEmailVerificationToken(body);
  const isJson = response.contentType.includes('application/json');
  const payload = response.body || response.statusText || '';

  return new NextResponse(isJson ? response.body : payload, {
    status: response.status,
    headers: {
      'content-type': isJson ? 'application/json' : 'text/plain',
    },
  });
}

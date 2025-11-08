import { NextResponse } from 'next/server';

import { listConversationsAction } from '../../(agent)/actions';

export async function GET() {
  const result = await listConversationsAction();
  const status = result.success ? 200 : 500;
  return NextResponse.json(result, { status });
}

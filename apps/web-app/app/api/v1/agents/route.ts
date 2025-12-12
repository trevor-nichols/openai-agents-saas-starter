import { NextResponse } from 'next/server';

import { listAvailableAgentsPage } from '@/lib/server/services/agents';
import { parseOptionalLimit } from '../_utils/pagination';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const limit = searchParams.get('limit');
  const cursor = searchParams.get('cursor');
  const search = searchParams.get('search');

  try {
    const parsedLimit = parseOptionalLimit(limit);
    if (!parsedLimit.ok) {
      return NextResponse.json({ message: parsedLimit.error }, { status: 400 });
    }

    const page = await listAvailableAgentsPage({
      limit: parsedLimit.value,
      cursor: cursor || null,
      search: search || null,
    });

    return NextResponse.json(page);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load agents.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

import { NextResponse } from 'next/server';

import { listWorkflows } from '@/lib/server/services/workflows';
import { parseOptionalLimit } from '../_utils/pagination';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  try {
    const parsedLimit = parseOptionalLimit(searchParams.get('limit'));
    if (!parsedLimit.ok) {
      return NextResponse.json({ message: parsedLimit.error }, { status: 400 });
    }

    const response = await listWorkflows({
      limit: parsedLimit.value,
      cursor: searchParams.get('cursor'),
      search: searchParams.get('search'),
    });

    return NextResponse.json(response ?? { items: [], next_cursor: null, total: 0 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load workflows';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

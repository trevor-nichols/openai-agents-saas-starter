import { NextResponse } from 'next/server';

import { listVectorStoresApiV1VectorStoresGet } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET() {
  try {
    const { client, auth } = await getServerApiClient();
    const res = await listVectorStoresApiV1VectorStoresGet({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
    });
    return NextResponse.json(res.data ?? { items: [], total: 0 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load vector stores';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

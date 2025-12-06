import { NextResponse } from 'next/server';

import { createContainerApiV1ContainersPost, listContainersApiV1ContainersGet } from '@/lib/api/client/sdk.gen';
import type { ContainerCreateRequest } from '@/lib/api/client/types.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET() {
  try {
    const { client, auth } = await getServerApiClient();
    const res = await listContainersApiV1ContainersGet({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
    });
    return NextResponse.json(res.data ?? { items: [], total: 0 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load containers';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as ContainerCreateRequest;
    const { client, auth } = await getServerApiClient();
    const res = await createContainerApiV1ContainersPost({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      body: payload,
    });
    if (!res.data) return NextResponse.json({ message: 'Create container missing data' }, { status: 500 });
    return NextResponse.json(res.data);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to create container';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

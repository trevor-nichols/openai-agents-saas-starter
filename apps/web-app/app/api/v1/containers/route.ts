import { NextResponse } from 'next/server';

import type { ContainerCreateRequest } from '@/lib/api/client/types.gen';
import { createContainer, listContainers } from '@/lib/server/services/containers';

export async function GET() {
  try {
    const res = await listContainers();
    return NextResponse.json(res ?? { items: [], total: 0 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load containers';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as ContainerCreateRequest;
    const res = await createContainer(payload);
    return NextResponse.json(res);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to create container';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

import { NextResponse } from 'next/server';

import {
  deleteContainerApiV1ContainersContainerIdDelete,
  getContainerByIdApiV1ContainersContainerIdGet,
} from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET(_req: Request, { params }: { params: Promise<{ containerId: string }> }) {
  const { containerId } = await params;
  try {
    const { client, auth } = await getServerApiClient();
    const res = await getContainerByIdApiV1ContainersContainerIdGet({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      path: { container_id: containerId },
    });
    if (!res.data) return NextResponse.json({ message: 'Container not found' }, { status: 404 });
    return NextResponse.json(res.data);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load container';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ containerId: string }> },
) {
  const { containerId } = await params;
  try {
    const { client, auth } = await getServerApiClient();
    await deleteContainerApiV1ContainersContainerIdDelete({
      client,
      auth,
      throwOnError: true,
      path: { container_id: containerId },
    });
    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to delete container';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

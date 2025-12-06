import { NextResponse } from 'next/server';

import { deleteObjectApiV1StorageObjectsObjectIdDelete } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ objectId: string }> },
) {
  const { objectId } = await params;
  try {
    const { client, auth } = await getServerApiClient();
    await deleteObjectApiV1StorageObjectsObjectIdDelete({
      client,
      auth,
      throwOnError: true,
      path: { object_id: objectId },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to delete object';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

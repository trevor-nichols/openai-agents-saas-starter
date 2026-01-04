import { NextResponse } from 'next/server';

import { deleteStorageObject } from '@/lib/server/services/storage';

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ objectId: string }> },
) {
  const { objectId } = await params;
  try {
    await deleteStorageObject(objectId);

    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to delete object';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

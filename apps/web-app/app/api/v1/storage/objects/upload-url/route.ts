import { NextResponse } from 'next/server';

import type { StoragePresignUploadRequest } from '@/lib/api/client/types.gen';
import { createPresignedUploadUrl } from '@/lib/server/services/storage';

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as StoragePresignUploadRequest;
    const response = await createPresignedUploadUrl(payload);
    return NextResponse.json(response);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to presign upload';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

import { NextResponse } from 'next/server';

import { downloadOpenAiFile } from '@/lib/server/services/openaiFiles';

type RouteParams = { params: Promise<{ fileId: string }> };

export async function GET(request: Request, { params }: RouteParams) {
  const { fileId } = await params;
  if (!fileId) {
    return NextResponse.json({ message: 'fileId is required.' }, { status: 400 });
  }

  try {
    const search = new URL(request.url).search;
    const result = await downloadOpenAiFile({ fileId, search, signal: request.signal });

    if (!result.ok || !result.stream) {
      const message = `Failed to download file (${result.status})`;
      return NextResponse.json({ message }, { status: result.status || 502 });
    }

    return new NextResponse(result.stream, {
      status: result.status,
      headers: result.headers,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to download file.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 502;
    return NextResponse.json({ message }, { status });
  }
}

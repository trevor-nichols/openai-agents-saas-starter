import { NextResponse } from 'next/server';

import { downloadOpenAiContainerFile } from '@/lib/server/services/openaiFiles';

type RouteParams = { params: Promise<{ containerId: string; fileId: string }> };

export async function GET(request: Request, { params }: RouteParams) {
  const { containerId, fileId } = await params;
  if (!containerId || !fileId) {
    return NextResponse.json({ message: 'containerId and fileId are required.' }, { status: 400 });
  }

  try {
    const search = new URL(request.url).search;
    const result = await downloadOpenAiContainerFile({ containerId, fileId, search });

    if (!result.ok || !result.stream) {
      const message = `Failed to download container file (${result.status})`;
      return NextResponse.json({ message }, { status: result.status || 502 });
    }

    return new NextResponse(result.stream, {
      status: result.status,
      headers: result.headers,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to download container file.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 502;
    return NextResponse.json({ message }, { status });
  }
}

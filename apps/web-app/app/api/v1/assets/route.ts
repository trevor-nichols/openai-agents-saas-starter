import { NextResponse } from 'next/server';

import { listAssets } from '@/lib/server/services/assets';
import { parseOptionalLimit } from '../_utils/pagination';

const ASSET_TYPES = new Set(['image', 'file']);
const SOURCE_TOOLS = new Set(['image_generation', 'code_interpreter', 'user_upload', 'unknown']);

function parseOptionalOffset(raw: string | null): number | undefined | { error: string } {
  if (!raw) {
    return undefined;
  }
  const value = Number.parseInt(raw, 10);
  if (!Number.isFinite(value) || Number.isNaN(value) || value < 0) {
    return { error: 'offset must be a non-negative integer' };
  }
  return value;
}

function parseOptionalInt(raw: string | null, label: string): number | undefined | { error: string } {
  if (!raw) {
    return undefined;
  }
  const value = Number.parseInt(raw, 10);
  if (!Number.isFinite(value) || Number.isNaN(value) || value < 0) {
    return { error: `${label} must be a non-negative integer` };
  }
  return value;
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const rawLimit = searchParams.get('limit');
  const rawOffset = searchParams.get('offset');
  const rawMessageId = searchParams.get('message_id');
  const assetType = searchParams.get('asset_type');
  const sourceTool = searchParams.get('source_tool');

  const parsedLimit = parseOptionalLimit(rawLimit);
  if (!parsedLimit.ok) {
    return NextResponse.json({ message: parsedLimit.error }, { status: 400 });
  }

  const offset = parseOptionalOffset(rawOffset);
  if (typeof offset === 'object') {
    return NextResponse.json({ message: offset.error }, { status: 400 });
  }

  const messageId = parseOptionalInt(rawMessageId, 'message_id');
  if (typeof messageId === 'object') {
    return NextResponse.json({ message: messageId.error }, { status: 400 });
  }

  if (assetType && !ASSET_TYPES.has(assetType)) {
    return NextResponse.json({ message: 'asset_type must be image or file' }, { status: 400 });
  }
  if (sourceTool && !SOURCE_TOOLS.has(sourceTool)) {
    return NextResponse.json(
      { message: 'source_tool must be image_generation, code_interpreter, user_upload, or unknown' },
      { status: 400 },
    );
  }

  try {
    const page = await listAssets({
      limit: parsedLimit.value,
      offset,
      assetType: assetType as 'image' | 'file' | null | undefined,
      sourceTool: sourceTool as
        | 'image_generation'
        | 'code_interpreter'
        | 'user_upload'
        | 'unknown'
        | null
        | undefined,
      conversationId: searchParams.get('conversation_id'),
      messageId,
      agentKey: searchParams.get('agent_key'),
      mimeTypePrefix: searchParams.get('mime_type_prefix'),
      createdAfter: searchParams.get('created_after'),
      createdBefore: searchParams.get('created_before'),
    });

    return NextResponse.json(page);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load assets.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

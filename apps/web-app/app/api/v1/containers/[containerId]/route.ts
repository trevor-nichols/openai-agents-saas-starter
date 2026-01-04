import { NextResponse } from 'next/server';

import { deleteContainer, getContainerById } from '@/lib/server/services/containers';

export async function GET(_req: Request, { params }: { params: Promise<{ containerId: string }> }) {
  const { containerId } = await params;
  try {
    const res = await getContainerById(containerId);
    return NextResponse.json(res);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load container';
    const normalized = message.toLowerCase();
    const status = normalized.includes('missing access token')
      ? 401
      : normalized.includes('not found')
        ? 404
        : 500;
    return NextResponse.json({ message }, { status });
  }
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ containerId: string }> },
) {
  const { containerId } = await params;
  try {
    await deleteContainer(containerId);
    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to delete container';
    const normalized = message.toLowerCase();
    const status = normalized.includes('missing access token')
      ? 401
      : normalized.includes('not found')
        ? 404
        : 500;
    return NextResponse.json({ message }, { status });
  }
}

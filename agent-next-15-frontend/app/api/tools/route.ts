import { NextResponse } from 'next/server';

import { listAvailableTools } from '@/lib/server/services/tools';

export async function GET() {
  try {
    const tools = await listAvailableTools();
    return NextResponse.json({
      success: true,
      tools,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load tools.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json(
      {
        success: false,
        error: message,
      },
      { status },
    );
  }
}

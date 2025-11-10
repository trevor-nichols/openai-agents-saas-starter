import { NextResponse } from 'next/server';

import { listAvailableAgents } from '@/lib/server/services/agents';

export async function GET() {
  try {
    const agents = await listAvailableAgents();
    return NextResponse.json(
      {
        success: true,
        agents,
      },
      { status: 200 },
    );
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load agents.';
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


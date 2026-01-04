import { NextResponse } from 'next/server';

import { getWorkflowDescriptor } from '@/lib/server/services/workflows';

export async function GET(_: Request, { params }: { params: Promise<{ workflowKey: string }> }) {
  const { workflowKey } = await params;
  try {
    const response = await getWorkflowDescriptor(workflowKey);

    if (!response) {
      return NextResponse.json({ message: 'Workflow not found' }, { status: 404 });
    }

    return NextResponse.json(response);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load workflow descriptor';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

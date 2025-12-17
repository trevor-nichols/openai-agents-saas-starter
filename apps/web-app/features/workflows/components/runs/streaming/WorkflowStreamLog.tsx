'use client';

import type { StreamingWorkflowEvent } from '@/lib/api/client/types.gen';
import { PublicSseStreamLog } from '@/components/ui/ai/public-sse-stream-log';

interface WorkflowStreamLogProps {
  events: (StreamingWorkflowEvent & { receivedAt?: string })[];
  className?: string;
}

export function WorkflowStreamLog({ events, className }: WorkflowStreamLogProps) {
  return <PublicSseStreamLog events={events} className={className} />;
}


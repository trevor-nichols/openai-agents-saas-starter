import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

import { WorkflowStreamLog } from '../WorkflowStreamLog';
import type { StreamingWorkflowEvent } from '@/lib/api/client/types.gen';
import type { GeneratedImageFrame } from '@/lib/streams/imageFrames';

beforeAll(() => {
  // Silence scrollTo in jsdom
  if (!HTMLElement.prototype.scrollTo) {
    HTMLElement.prototype.scrollTo = () => {};
  }
});

beforeEach(() => {
  vi.clearAllMocks();
});

const fileSearchEvent: StreamingWorkflowEvent = {
  schema: 'public_sse_v1',
  event_id: 1,
  stream_id: 'stream-test',
  server_timestamp: '2025-12-15T00:00:00.000Z',
  kind: 'tool.status',
  conversation_id: 'conv-1',
  response_id: 'resp-1',
  agent: 'triage',
  output_index: 0,
  item_id: 'fs-1',
  workflow: {
    workflow_key: 'wf-1',
    workflow_run_id: 'run-1',
    stage_name: 'main',
    step_name: 'step-1',
    step_agent: 'triage',
    parallel_group: null,
    branch_index: null,
  },
  tool: {
    tool_type: 'file_search',
    tool_call_id: 'fs-1',
    status: 'completed',
    queries: ['report'],
    results: [
      {
        file_id: 'file-1',
        filename: 'report.pdf',
        score: 0.91,
        vector_store_id: 'vs-1',
        text: 'Quarterly summary',
      },
    ],
  },
};

const imageFrames: GeneratedImageFrame[] = [
  {
    id: 'img-1:0',
    status: 'completed',
    src: 'data:image/png;base64,aGVsbG8=',
    outputIndex: 0,
    revisedPrompt: 'Final frame',
  },
];

const imageGenerationEvent: StreamingWorkflowEvent = {
  schema: 'public_sse_v1',
  event_id: 2,
  stream_id: 'stream-test',
  server_timestamp: '2025-12-15T00:00:00.050Z',
  kind: 'tool.output',
  conversation_id: 'conv-1',
  response_id: 'resp-1',
  agent: 'triage',
  output_index: 1,
  item_id: 'img-1',
  workflow: {
    workflow_key: 'wf-1',
    workflow_run_id: 'run-1',
    stage_name: 'main',
    step_name: 'step-1',
    step_agent: 'triage',
    parallel_group: null,
    branch_index: null,
  },
  tool_call_id: 'img-1',
  tool_type: 'image_generation',
  output: imageFrames,
};

describe('WorkflowStreamLog tool outputs', () => {
  it('renders file search results with custom renderer', () => {
    render(<WorkflowStreamLog events={[fileSearchEvent]} />);

    fireEvent.click(screen.getByRole('button', { name: /tool-file_search/i }));

    expect(screen.getByText('report.pdf')).toBeInTheDocument();
    expect(screen.getByText('(file-1)')).toBeInTheDocument();
  });

  it('renders image generation frames', () => {
    render(<WorkflowStreamLog events={[imageGenerationEvent]} />);

    fireEvent.click(screen.getByRole('button', { name: /tool-image_generation/i }));

    const img = screen.getByRole('img');
    expect(img).toBeInTheDocument();
    expect(img.getAttribute('src')).toContain('data:image/png;base64');
  });
});

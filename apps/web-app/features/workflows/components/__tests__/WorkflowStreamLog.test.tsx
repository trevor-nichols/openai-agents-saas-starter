import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

import { WorkflowStreamLog } from '../WorkflowStreamLog';
import type { StreamingWorkflowEvent } from '@/lib/api/client/types.gen';

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
  kind: 'run_item_stream_event',
  event: 'tool_call',
  sequence_number: 1,
  tool_call: {
    tool_type: 'file_search',
    file_search_call: {
      id: 'fs-1',
      type: 'file_search_call',
      status: 'searching',
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
  },
};

const imageGenerationEvent: StreamingWorkflowEvent = {
  kind: 'run_item_stream_event',
  event: 'tool_call',
  sequence_number: 2,
  tool_call: {
    tool_type: 'image_generation',
    image_generation_call: {
      id: 'img-1',
      type: 'image_generation_call',
      status: 'partial_image',
      result: 'data:image/png;base64,aGVsbG8=',
      format: 'png',
    },
  },
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

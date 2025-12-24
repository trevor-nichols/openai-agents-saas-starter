import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { WorkflowAgentNodePreviewList } from '../WorkflowAgentNodePreviewList';
import type { WorkflowNodePreviewSnapshot } from '@/lib/workflows/streaming';

const emptyPreview: WorkflowNodePreviewSnapshot = {
  hasContent: false,
  lastUpdatedAt: null,
  lifecycleStatus: null,
  items: [],
  overflowCount: 0,
};

describe('WorkflowAgentNodePreviewList', () => {
  it('renders the status description when no preview items exist', () => {
    render(
      <WorkflowAgentNodePreviewList
        preview={emptyPreview}
        statusDescription="Awaiting execution."
      />,
    );

    expect(screen.getByText('Awaiting execution.')).toBeInTheDocument();
  });

  it('renders tool, refusal, and message items with overflow count', () => {
    const preview: WorkflowNodePreviewSnapshot = {
      ...emptyPreview,
      hasContent: true,
      items: [
        {
          kind: 'tool',
          itemId: 'tool-1',
          outputIndex: 0,
          label: 'Web Search',
          status: 'running',
          inputPreview: 'q=workflows',
        },
        {
          kind: 'refusal',
          itemId: 'refusal-1',
          outputIndex: 1,
          text: 'Cannot comply with the request.',
          isDone: true,
        },
        {
          kind: 'message',
          itemId: 'message-1',
          outputIndex: 2,
          text: 'Pipeline summary is ready.',
          isDone: true,
        },
      ],
      overflowCount: 2,
    };

    render(
      <WorkflowAgentNodePreviewList
        preview={preview}
        statusDescription="Awaiting execution."
      />,
    );

    expect(screen.getByText('Web Search')).toBeInTheDocument();
    expect(screen.getByText('running')).toBeInTheDocument();
    expect(screen.getByText('Cannot comply with the request.')).toBeInTheDocument();
    expect(screen.getByText('Pipeline summary is ready.')).toBeInTheDocument();
    expect(screen.getByText(/\+2 more/)).toBeInTheDocument();
  });
});

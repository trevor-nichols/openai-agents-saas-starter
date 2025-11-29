import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';

import { WorkflowStreamLog } from '../WorkflowStreamLog';

describe('WorkflowStreamLog', () => {
  beforeAll(() => {
    Object.defineProperty(window.HTMLElement.prototype, 'scrollTo', {
      value: vi.fn(),
      writable: true,
    });
  });

  it('renders events with labels and payload', () => {
    const events = [
      {
        kind: 'raw_response' as const,
        workflow_key: 'demo',
        workflow_run_id: 'run-1',
        raw_type: 'response.output_text.delta',
        text_delta: 'Hello',
        sequence_number: 1,
        is_terminal: false,
      },
      {
        kind: 'lifecycle' as const,
        workflow_key: 'demo',
        workflow_run_id: 'run-1',
        event: 'completed',
        sequence_number: 2,
        is_terminal: true,
      },
    ];

    render(<WorkflowStreamLog events={events} />);

    expect(screen.getByText('Response')).toBeInTheDocument();
    expect(screen.getByText('Lifecycle')).toBeInTheDocument();
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Terminal')).toBeInTheDocument();
  });
});

import { render, screen } from '@testing-library/react';

import { GuardrailEventsPanel } from '../GuardrailEventsPanel';
import type { StreamingChatEvent } from '@/lib/api/client/types.gen';

describe('GuardrailEventsPanel', () => {
  const baseEvent: StreamingChatEvent = {
    kind: 'guardrail_result',
    conversation_id: 'c1',
    guardrail_key: 'pii',
    guardrail_name: 'PII Masking',
    guardrail_stage: 'input',
    guardrail_confidence: 0.87,
  };

  it('renders nothing when there are no guardrail events', () => {
    render(<GuardrailEventsPanel events={[]} />);
    expect(screen.queryByText(/Guardrail/)).toBeNull();
  });

  it('renders guardrail metadata and masked content', () => {
    render(
      <GuardrailEventsPanel
        events={[
          {
            ...baseEvent,
            guardrail_masked_content: '***redacted***',
            guardrail_tripwire_triggered: true,
            guardrail_flagged: true,
            guardrail_suppressed: false,
          },
        ]}
      />,
    );

    expect(screen.getByText('Guardrail')).toBeInTheDocument();
    expect(screen.getByText('Stage: input')).toBeInTheDocument();
    expect(screen.getByText('Key: pii')).toBeInTheDocument();
    expect(screen.getByText('Name: PII Masking')).toBeInTheDocument();
    expect(screen.getByText(/Tripwire: yes/)).toBeInTheDocument();
    expect(screen.getByText(/Flagged: yes/)).toBeInTheDocument();
    expect(screen.getByText(/Suppressed: no/)).toBeInTheDocument();
    expect(screen.getAllByText('***redacted***').length).toBeGreaterThan(0);
  });

  it('renders details and token usage JSON blobs', () => {
    render(
      <GuardrailEventsPanel
        events={[
          {
            ...baseEvent,
            guardrail_details: { rule: 'contains_email' },
            guardrail_token_usage: { input_tokens: 10 },
          },
        ]}
      />,
    );

    expect(screen.getAllByText(/contains_email/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/input_tokens/).length).toBeGreaterThan(0);
  });
});

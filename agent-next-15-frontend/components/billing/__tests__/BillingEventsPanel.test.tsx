import { render, screen } from '@testing-library/react';
import React from 'react';

import BillingEventsPanel from '../BillingEventsPanel';

const sampleEvents = [
  {
    tenant_id: 'tenant-1',
    event_type: 'invoice.paid',
    stripe_event_id: 'evt_1',
    occurred_at: '2025-11-07T10:00:00Z',
    summary: 'Invoice paid',
    status: 'processed',
  },
];

describe('BillingEventsPanel', () => {
  it('renders billing events', () => {
    render(<BillingEventsPanel events={sampleEvents} status="open" />);
    expect(screen.getByText('invoice paid')).toBeInTheDocument();
    expect(screen.getByText('Invoice paid')).toBeInTheDocument();
    expect(screen.getByText(/live/i)).toBeInTheDocument();
  });
});

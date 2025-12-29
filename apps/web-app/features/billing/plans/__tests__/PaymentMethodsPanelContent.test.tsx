import { render, screen } from '@testing-library/react';

import { PaymentMethodsPanelContent } from '../components/PaymentMethodsPanelContent';

const baseProps = {
  paymentMethods: [],
  isLoading: false,
  error: null,
  onRetry: async () => {},
  onAdd: () => {},
  onSetDefault: () => {},
  onRequestDetach: () => {},
  isAdding: false,
  stripeEnabled: true,
  canAdd: true,
  isSettingDefaultId: null,
  isDetachingId: null,
};

describe('PaymentMethodsPanelContent', () => {
  it('renders the empty state when no payment methods exist', () => {
    render(<PaymentMethodsPanelContent {...baseProps} />);

    expect(screen.getByText(/no payment methods saved/i)).toBeInTheDocument();
    expect(screen.getByText(/add a card to keep subscription changes/i)).toBeInTheDocument();
  });

  it('renders the default card helper when a default method exists', () => {
    render(
      <PaymentMethodsPanelContent
        {...baseProps}
        paymentMethods={[
          { id: 'pm_default', brand: 'visa', last4: '4242', exp_month: 12, exp_year: 2027, is_default: true },
          { id: 'pm_secondary', brand: 'mastercard', last4: '5555', exp_month: 6, exp_year: 2028, is_default: false },
        ]}
      />,
    );

    expect(screen.getByText(/default card.*4242.*renewals/i)).toBeInTheDocument();
  });

  it('renders the error state message when an error is present', () => {
    render(
      <PaymentMethodsPanelContent
        {...baseProps}
        error="Failed to load payment methods."
      />,
    );

    expect(screen.getByText(/unable to load payment methods/i)).toBeInTheDocument();
    expect(screen.getByText(/failed to load payment methods/i)).toBeInTheDocument();
  });
});

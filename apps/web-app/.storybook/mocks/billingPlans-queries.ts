export function useBillingPlans() {
  return {
    plans: [
      { code: 'starter', name: 'Starter', price_cents: 4900, currency: 'USD', interval: 'month', interval_count: 1, trial_days: 14, seat_included: 3, feature_toggles: {}, features: [], is_active: true },
      { code: 'pro', name: 'Pro', price_cents: 14900, currency: 'USD', interval: 'month', interval_count: 1, trial_days: 0, seat_included: 10, feature_toggles: {}, features: [], is_active: true },
    ],
    isLoading: false,
    error: null,
    refetch: async () => {},
  };
}

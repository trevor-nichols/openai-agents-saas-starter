## apps/web-app/features

| Name | Purpose | Location | Required | Default | Format | Sensitivity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Enables Stripe Elements for collecting payment methods in the billing portal. | `billing/plans/components/PaymentMethodSetupDialog.tsx` (referenced in UI fallback text); `billing/plans/hooks/usePaymentMethodsPanel.ts` (referenced in error message) | Optional (Billing payment entry features are disabled if missing) | - | String (pk_test_...) | Non-secret |
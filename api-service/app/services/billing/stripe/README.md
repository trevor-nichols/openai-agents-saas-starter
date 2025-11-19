# Billing ▸ Stripe Subdomain

Contains Stripe-specific dispatchers, retry workers, and event schemas (`stripe_dispatcher`, `stripe_retry_worker`, `stripe_event_models`). Keeping them under `billing/stripe` isolates third-party glue from generic billing workflows.

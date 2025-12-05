# Services Dependency Snapshot
_Generated: 2025-11-17 21:02:02 UTC_

## Summary
- Total modules scanned: 39
- Modules with no internal deps: 23
- Modules not referenced internally: 22

### Top Fan-Out (depends on most peers)
- `app.services.auth.builders` → 5 modules
- `app.services.signup.signup_service` → 4 modules
- `app.services.auth_service` → 4 modules
- `app.services.auth.session_service` → 4 modules
- `app.services.signup.signup_request_service` → 2 modules

### Top Fan-In (referenced by most peers)
- `app.services.users.service` ← 4 modules
- `app.services.auth_service` ← 4 modules
- `app.services.auth.errors` ← 4 modules
- `app.services.geoip_service` ← 3 modules
- `app.services.billing.stripe.event_models` ← 3 modules

## Adjacency
| Module | Internal Dependencies |
| --- | --- |
| `app.services` | — |
| `app.services.agent_service` | `app.services.conversation_service` |
| `app.services.auth` | — |
| `app.services.auth.builders` | `app.services.auth`<br>`app.services.auth.service_account_service`<br>`app.services.auth.session_service`<br>`app.services.geoip_service`<br>`app.services.users.service` |
| `app.services.auth.errors` | — |
| `app.services.auth.refresh_token_manager` | — |
| `app.services.auth.service_account_service` | `app.services.auth.errors`<br>`app.services.auth.refresh_token_manager` |
| `app.services.auth.session_service` | `app.services.auth.errors`<br>`app.services.auth.refresh_token_manager`<br>`app.services.auth.session_store`<br>`app.services.users.service` |
| `app.services.auth.session_store` | `app.services.geoip_service` |
| `app.services.auth_service` | `app.services.auth`<br>`app.services.auth.errors`<br>`app.services.geoip_service`<br>`app.services.users.service` |
| `app.services.billing` | — |
| `app.services.billing.billing_events` | `app.services.billing.stripe.event_models` |
| `app.services.billing.billing_service` | `app.services.billing.payment_gateway` |
| `app.services.billing.payment_gateway` | — |
| `app.services.billing.stripe` | — |
| `app.services.billing.stripe.dispatcher` | `app.services.billing.billing_service`<br>`app.services.billing.stripe.event_models` |
| `app.services.billing.stripe.event_models` | — |
| `app.services.billing.stripe.retry_worker` | `app.services.billing.stripe.dispatcher`<br>`app.services.billing.stripe.event_models` |
| `app.services.conversation_service` | — |
| `app.services.conversations` | — |
| `app.services.geoip_service` | — |
| `app.services.integrations` | — |
| `app.services.service_account_bridge` | `app.services.auth.errors`<br>`app.services.auth_service` |
| `app.services.shared` | — |
| `app.services.shared.rate_limit_service` | — |
| `app.services.signup` | — |
| `app.services.signup.email_verification_service` | `app.services.auth_service` |
| `app.services.signup.invite_service` | — |
| `app.services.signup.password_recovery_service` | `app.services.auth_service`<br>`app.services.users.service` |
| `app.services.signup.signup_request_service` | `app.services.shared.rate_limit_service`<br>`app.services.signup.invite_service` |
| `app.services.signup.signup_service` | `app.services.auth_service`<br>`app.services.billing.billing_service`<br>`app.services.signup.email_verification_service`<br>`app.services.signup.invite_service` |
| `app.services.status` | — |
| `app.services.status.status_alert_dispatcher` | — |
| `app.services.status.status_service` | — |
| `app.services.status.status_subscription_service` | `app.services.shared.rate_limit_service` |
| `app.services.tenant` | — |
| `app.services.tenant.tenant_settings_service` | — |
| `app.services.users` | — |
| `app.services.users.service` | — |

## Reverse References
| Module | Referenced By |
| --- | --- |
| `app.services` | — |
| `app.services.agent_service` | — |
| `app.services.auth` | `app.services.auth.builders`<br>`app.services.auth_service` |
| `app.services.auth.builders` | — |
| `app.services.auth.errors` | `app.services.auth.service_account_service`<br>`app.services.auth.session_service`<br>`app.services.auth_service`<br>`app.services.service_account_bridge` |
| `app.services.auth.refresh_token_manager` | `app.services.auth.service_account_service`<br>`app.services.auth.session_service` |
| `app.services.auth.service_account_service` | `app.services.auth.builders` |
| `app.services.auth.session_service` | `app.services.auth.builders` |
| `app.services.auth.session_store` | `app.services.auth.session_service` |
| `app.services.auth_service` | `app.services.service_account_bridge`<br>`app.services.signup.email_verification_service`<br>`app.services.signup.password_recovery_service`<br>`app.services.signup.signup_service` |
| `app.services.billing` | — |
| `app.services.billing.billing_events` | — |
| `app.services.billing.billing_service` | `app.services.billing.stripe.dispatcher`<br>`app.services.signup.signup_service` |
| `app.services.billing.payment_gateway` | `app.services.billing.billing_service` |
| `app.services.billing.stripe` | — |
| `app.services.billing.stripe.dispatcher` | `app.services.billing.stripe.retry_worker` |
| `app.services.billing.stripe.event_models` | `app.services.billing.billing_events`<br>`app.services.billing.stripe.dispatcher`<br>`app.services.billing.stripe.retry_worker` |
| `app.services.billing.stripe.retry_worker` | — |
| `app.services.conversation_service` | `app.services.agent_service` |
| `app.services.conversations` | — |
| `app.services.geoip_service` | `app.services.auth.builders`<br>`app.services.auth.session_store`<br>`app.services.auth_service` |
| `app.services.integrations` | — |
| `app.services.service_account_bridge` | — |
| `app.services.shared` | — |
| `app.services.shared.rate_limit_service` | `app.services.signup.signup_request_service`<br>`app.services.status.status_subscription_service` |
| `app.services.signup` | — |
| `app.services.signup.email_verification_service` | `app.services.signup.signup_service` |
| `app.services.signup.invite_service` | `app.services.signup.signup_request_service`<br>`app.services.signup.signup_service` |
| `app.services.signup.password_recovery_service` | — |
| `app.services.signup.signup_request_service` | — |
| `app.services.signup.signup_service` | — |
| `app.services.status` | — |
| `app.services.status.status_alert_dispatcher` | — |
| `app.services.status.status_service` | — |
| `app.services.status.status_subscription_service` | — |
| `app.services.tenant` | — |
| `app.services.tenant.tenant_settings_service` | — |
| `app.services.users` | — |
| `app.services.users.service` | `app.services.auth.builders`<br>`app.services.auth.session_service`<br>`app.services.auth_service`<br>`app.services.signup.password_recovery_service` |

> Generated by `tools/moduleviz.py`.

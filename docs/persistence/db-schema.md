# Database Schema (Full, from SQLAlchemy models)

**Source model files used (from your paste):**

* `types.py`
* `activity/models.py`
* `auth/models.py`
* `billing/models.py`
* `containers/models.py`
* `conversations/models.py`
* `conversations/ledger_models.py`
* `status/models.py`
* `storage/models.py`
* `stripe/models.py`
* `tenants/models.py`
* `vector_stores/models.py`
* `workflows/models.py`

## Type notes (important for correctness)

* **`CITEXTCompat`** → Postgres: `CITEXT`, otherwise falls back to `VARCHAR(255)`
* **`JSONBCompat`** → Postgres: `JSONB`, otherwise falls back to `JSON`
* **`INT_PK_TYPE`** → Postgres: `BIGINT`, SQLite: `INTEGER` (used for autoincrement PKs)

---

## Table inventory (all tables found)

### Core / Tenants

* `tenant_accounts`
* `tenant_settings`

### Auth

* `users`
* `user_profiles`
* `tenant_user_memberships`
* `password_history`
* `user_login_events`
* `tenant_signup_requests`
* `tenant_signup_invites`
* `tenant_signup_invite_reservations`
* `user_sessions`
* `service_account_tokens`
* `user_mfa_methods`
* `user_recovery_codes`
* `user_consents`
* `user_notification_preferences`
* `usage_counters`
* `security_events`

### Activity

* `activity_events`
* `activity_event_receipts`
* `activity_last_seen`

### Conversations

* `agent_conversations`
* `agent_messages`
* `conversation_summaries`
* `agent_run_events`
* `agent_run_usage`

### Conversation Ledger (public_sse_v1 replay)

* `conversation_ledger_segments`
* `conversation_ledger_events`
* `conversation_run_queue_items`

### Billing

* `billing_plans`
* `plan_features`
* `tenant_subscriptions`
* `subscription_invoices`
* `subscription_usage`

### Stripe

* `stripe_events`
* `stripe_event_dispatch`

### Containers

* `containers`
* `agent_containers`

### Storage

* `storage_buckets`
* `storage_objects`

### Vector Stores

* `vector_stores`
* `vector_store_files`
* `agent_vector_stores`

### Status

* `status_subscriptions`

### Workflows

* `workflow_runs`
* `workflow_run_steps`

---

# Detailed schema

## Core / Tenants

## `tenant_accounts` (from `conversations/models.py`)

Represents a customer tenant.

| Column       | Type         | Null | Default     | Notes  |
| ------------ | ------------ | ---- | ----------- | ------ |
| `id`         | UUID         | NO   | `uuid_pk()` |        |
| `slug`       | String(64)   | NO   | —           | unique |
| `name`       | String(128)  | NO   | —           |        |
| `created_at` | DateTime(tz) | NO   | `UTC_NOW`   |        |

**Constraints**

* PK: `id`
* Unique: `slug`

---

## `tenant_settings` (from `tenants/models.py`)

Per-tenant settings / metadata.

| Column                  | Type         | Null | Default        | Notes                     |
| ----------------------- | ------------ | ---- | -------------- | ------------------------- |
| `id`                    | UUID         | NO   | `uuid.uuid4()` |                           |
| `tenant_id`             | UUID         | NO   | —              | FK → `tenant_accounts.id` |
| `billing_contacts_json` | JSONB/JSON   | NO   | `list`         |                           |
| `billing_webhook_url`   | String(512)  | YES  | —              |                           |
| `plan_metadata_json`    | JSONB/JSON   | NO   | `dict`         |                           |
| `flags_json`            | JSONB/JSON   | NO   | `dict`         |                           |
| `version`               | Integer      | NO   | `1`            | optimistic lock counter   |
| `created_at`            | DateTime(tz) | NO   | `UTC_NOW`      |                           |
| `updated_at`            | DateTime(tz) | NO   | `UTC_NOW`      | `onupdate=UTC_NOW`        |

**Constraints**

* PK: `id`
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* Unique: `tenant_id`

---

## Auth (from `auth/models.py`)

## `users`

Human identity.

| Column                    | Type                | Null | Default     | Notes                                   |
| ------------------------- | ------------------- | ---- | ----------- | --------------------------------------- |
| `id`                      | UUID                | NO   | `uuid_pk()` |                                         |
| `email`                   | CITEXT/VARCHAR      | NO   | —           | `CITEXTCompat()`, unique via constraint |
| `password_hash`           | Text                | NO   | —           |                                         |
| `password_pepper_version` | String(32)          | NO   | `"v2"`      |                                         |
| `status`                  | Enum(`user_status`) | NO   | `pending`   | values: pending/active/disabled/locked  |
| `platform_role`           | Enum(`platform_role`) | YES | —         | values: platform_operator               |
| `email_verified_at`       | DateTime(tz)        | YES  | —           |                                         |
| `created_at`              | DateTime(tz)        | NO   | `UTC_NOW`   |                                         |
| `updated_at`              | DateTime(tz)        | NO   | `UTC_NOW`   | `onupdate=UTC_NOW`                      |

**Constraints**

* PK: `id`
* Unique: `email`
* Index: `ix_users_status(status)`

---

## `user_profiles`

Optional display/profile info.

| Column          | Type         | Null | Default     | Notes              |
| --------------- | ------------ | ---- | ----------- | ------------------ |
| `id`            | UUID         | NO   | `uuid_pk()` |                    |
| `user_id`       | UUID         | NO   | —           | FK → `users.id`    |
| `display_name`  | String(128)  | YES  | —           |                    |
| `given_name`    | String(64)   | YES  | —           |                    |
| `family_name`   | String(64)   | YES  | —           |                    |
| `avatar_url`    | String(512)  | YES  | —           |                    |
| `timezone`      | String(64)   | YES  | —           |                    |
| `locale`        | String(32)   | YES  | —           |                    |
| `metadata_json` | JSONB/JSON   | YES  | —           | `JSONBCompat`      |
| `created_at`    | DateTime(tz) | NO   | `UTC_NOW`   |                    |
| `updated_at`    | DateTime(tz) | NO   | `UTC_NOW`   | `onupdate=UTC_NOW` |

**Constraints**

* PK: `id`
* FK: `user_id` → `users.id` (CASCADE)

---

## `tenant_user_memberships`

User ↔ tenant association with role.

| Column       | Type         | Null | Default     | Notes                     |
| ------------ | ------------ | ---- | ----------- | ------------------------- |
| `id`         | UUID         | NO   | `uuid_pk()` |                           |
| `user_id`    | UUID         | NO   | —           | FK → `users.id`           |
| `tenant_id`  | UUID         | NO   | —           | FK → `tenant_accounts.id` |
| `role`       | Enum(`tenant_role`) | NO | —        | values: owner/admin/member/viewer |
| `created_at` | DateTime(tz) | NO   | `UTC_NOW`   |                           |

**Constraints**

* PK: `id`
* FK: `user_id` → `users.id` (CASCADE)
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* Unique: (`user_id`, `tenant_id`)
* Index: `ix_tenant_user_memberships_tenant_role(tenant_id, role)`
* Index: `ix_tenant_user_memberships_user(user_id)`

---

## `password_history`

Historical password hashes for reuse prevention.

| Column                    | Type         | Null | Default     | Notes           |
| ------------------------- | ------------ | ---- | ----------- | --------------- |
| `id`                      | UUID         | NO   | `uuid_pk()` |                 |
| `user_id`                 | UUID         | NO   | —           | FK → `users.id` |
| `password_hash`           | Text         | NO   | —           |                 |
| `password_pepper_version` | String(32)   | NO   | —           |                 |
| `created_at`              | DateTime(tz) | NO   | `UTC_NOW`   |                 |

**Constraints**

* PK: `id`
* FK: `user_id` → `users.id` (CASCADE)
* Index: `ix_password_history_user_created(user_id, created_at)`

---

## `user_login_events`

Immutable audit log for login attempts.

| Column       | Type         | Null | Default     | Notes                                  |
| ------------ | ------------ | ---- | ----------- | -------------------------------------- |
| `id`         | UUID         | NO   | `uuid_pk()` |                                        |
| `user_id`    | UUID         | NO   | —           | FK → `users.id`                        |
| `tenant_id`  | UUID         | YES  | —           | FK → `tenant_accounts.id` (`SET NULL`) |
| `ip_hash`    | String(128)  | NO   | —           |                                        |
| `user_agent` | String(512)  | YES  | —           |                                        |
| `result`     | String(16)   | NO   | —           | e.g. success/failure/locked            |
| `reason`     | String(128)  | YES  | —           |                                        |
| `created_at` | DateTime(tz) | NO   | `UTC_NOW`   |                                        |

**Constraints**

* PK: `id`
* FK: `user_id` → `users.id` (CASCADE)
* FK: `tenant_id` → `tenant_accounts.id` (SET NULL)
* Index: `ix_user_login_events_user_created(user_id, created_at)`
* Index: `ix_user_login_events_tenant_created(tenant_id, created_at)`

---

## `tenant_signup_requests`

Access requests when approval/invite-only flows are enabled.

| Column              | Type                                 | Null | Default     | Notes                        |
| ------------------- | ------------------------------------ | ---- | ----------- | ---------------------------- |
| `id`                | UUID                                 | NO   | `uuid_pk()` |                              |
| `email`             | CITEXT/VARCHAR                       | NO   | —           | `CITEXTCompat()`             |
| `organization`      | String(128)                          | YES  | —           |                              |
| `full_name`         | String(128)                          | YES  | —           |                              |
| `message`           | Text                                 | YES  | —           |                              |
| `status`            | Enum(`tenant_signup_request_status`) | NO   | `pending`   |                              |
| `decision_reason`   | Text                                 | YES  | —           |                              |
| `decided_at`        | DateTime(tz)                         | YES  | —           |                              |
| `decided_by`        | UUID                                 | YES  | —           | FK → `users.id` (`SET NULL`) |
| `invite_token_hint` | String(16)                           | YES  | —           |                              |
| `ip_address`        | String(64)                           | YES  | —           |                              |
| `user_agent`        | String(512)                          | YES  | —           |                              |
| `honeypot_value`    | String(64)                           | YES  | —           |                              |
| `metadata_json`     | JSONB/JSON                           | YES  | `None`      |                              |
| `created_at`        | DateTime(tz)                         | NO   | `UTC_NOW`   |                              |
| `updated_at`        | DateTime(tz)                         | NO   | `UTC_NOW`   | `onupdate=UTC_NOW`           |

**Constraints**

* PK: `id`
* FK: `decided_by` → `users.id` (SET NULL)
* Index: `ix_tenant_signup_requests_status(status)`
* Index: `ix_tenant_signup_requests_email(email)`

---

## `tenant_signup_invites`

Operator-issued invites to gate signups.

| Column              | Type                                | Null | Default     | Notes                                         |
| ------------------- | ----------------------------------- | ---- | ----------- | --------------------------------------------- |
| `id`                | UUID                                | NO   | `uuid_pk()` |                                               |
| `token_hash`        | String(128)                         | NO   | —           | unique via constraint                         |
| `token_hint`        | String(16)                          | NO   | —           |                                               |
| `invited_email`     | CITEXT/VARCHAR                      | YES  | —           |                                               |
| `issuer_user_id`    | UUID                                | YES  | —           | FK → `users.id` (`SET NULL`)                  |
| `issuer_tenant_id`  | UUID                                | YES  | —           | FK → `tenant_accounts.id` (`SET NULL`)        |
| `signup_request_id` | UUID                                | YES  | —           | FK → `tenant_signup_requests.id` (`SET NULL`) |
| `status`            | Enum(`tenant_signup_invite_status`) | NO   | `active`    |                                               |
| `max_redemptions`   | Integer                             | NO   | `1`         |                                               |
| `redeemed_count`    | Integer                             | NO   | `0`         |                                               |
| `expires_at`        | DateTime(tz)                        | YES  | —           |                                               |
| `last_redeemed_at`  | DateTime(tz)                        | YES  | —           |                                               |
| `revoked_at`        | DateTime(tz)                        | YES  | —           |                                               |
| `revoked_reason`    | Text                                | YES  | —           |                                               |
| `note`              | Text                                | YES  | —           |                                               |
| `metadata_json`     | JSONB/JSON                          | YES  | `None`      |                                               |
| `created_at`        | DateTime(tz)                        | NO   | `UTC_NOW`   |                                               |
| `updated_at`        | DateTime(tz)                        | NO   | `UTC_NOW`   | `onupdate=UTC_NOW`                            |

**Constraints**

* PK: `id`
* Unique: `token_hash`
* FK: `issuer_user_id` → `users.id` (SET NULL)
* FK: `issuer_tenant_id` → `tenant_accounts.id` (SET NULL)
* FK: `signup_request_id` → `tenant_signup_requests.id` (SET NULL)
* Index: `ix_tenant_signup_invites_status(status)`

---

## `tenant_signup_invite_reservations`

In-flight invite reservations while signup completes.

| Column            | Type                                     | Null | Default     | Notes                                  |
| ----------------- | ---------------------------------------- | ---- | ----------- | -------------------------------------- |
| `id`              | UUID                                     | NO   | `uuid_pk()` |                                        |
| `invite_id`       | UUID                                     | NO   | —           | FK → `tenant_signup_invites.id`        |
| `email`           | CITEXT/VARCHAR                           | NO   | —           |                                        |
| `status`          | Enum(`signup_invite_reservation_status`) | NO   | `active`    |                                        |
| `reserved_at`     | DateTime(tz)                             | NO   | `UTC_NOW`   |                                        |
| `expires_at`      | DateTime(tz)                             | NO   | —           |                                        |
| `released_at`     | DateTime(tz)                             | YES  | —           |                                        |
| `released_reason` | Text                                     | YES  | —           |                                        |
| `finalized_at`    | DateTime(tz)                             | YES  | —           |                                        |
| `tenant_id`       | UUID                                     | YES  | —           | FK → `tenant_accounts.id` (`SET NULL`) |
| `user_id`         | UUID                                     | YES  | —           | FK → `users.id` (`SET NULL`)           |
| `created_at`      | DateTime(tz)                             | NO   | `UTC_NOW`   |                                        |
| `updated_at`      | DateTime(tz)                             | NO   | `UTC_NOW`   | `onupdate=UTC_NOW`                     |

**Constraints**

* PK: `id`
* FK: `invite_id` → `tenant_signup_invites.id` (CASCADE)
* FK: `tenant_id` → `tenant_accounts.id` (SET NULL)
* FK: `user_id` → `users.id` (SET NULL)
* Index: `ix_signup_invite_reservations_status(status)`
* Index: `ix_signup_invite_reservations_invite_status(invite_id, status)`
* Index: `ix_signup_invite_reservations_expires(expires_at)`

---

## `user_sessions`

Normalized device/session metadata for active refresh tokens.

| Column             | Type         | Null | Default     | Notes                     |
| ------------------ | ------------ | ---- | ----------- | ------------------------- |
| `id`               | UUID         | NO   | `uuid_pk()` |                           |
| `user_id`          | UUID         | NO   | —           | FK → `users.id`           |
| `tenant_id`        | UUID         | NO   | —           | FK → `tenant_accounts.id` |
| `refresh_jti`      | String(64)   | NO   | —           | unique (also indexed)     |
| `fingerprint`      | String(256)  | YES  | —           |                           |
| `ip_hash`          | String(128)  | YES  | —           |                           |
| `ip_encrypted`     | LargeBinary  | YES  | —           |                           |
| `ip_masked`        | String(64)   | YES  | —           |                           |
| `user_agent`       | String(512)  | YES  | —           |                           |
| `client_platform`  | String(64)   | YES  | —           |                           |
| `client_browser`   | String(64)   | YES  | —           |                           |
| `client_device`    | String(32)   | YES  | —           |                           |
| `location_city`    | String(128)  | YES  | —           |                           |
| `location_region`  | String(128)  | YES  | —           |                           |
| `location_country` | String(64)   | YES  | —           |                           |
| `created_at`       | DateTime(tz) | NO   | `UTC_NOW`   |                           |
| `updated_at`       | DateTime(tz) | NO   | `UTC_NOW`   | `onupdate=UTC_NOW`        |
| `last_seen_at`     | DateTime(tz) | YES  | —           |                           |
| `revoked_at`       | DateTime(tz) | YES  | —           |                           |
| `revoked_reason`   | String(256)  | YES  | —           |                           |

**Constraints**

* PK: `id`
* FK: `user_id` → `users.id` (CASCADE)
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* Unique: `refresh_jti`
* Index: `ix_user_sessions_user_last_seen(user_id, last_seen_at)`
* Index: `ix_user_sessions_tenant_last_seen(tenant_id, last_seen_at)`
* Index: `ix_user_sessions_refresh_jti(refresh_jti)` (unique)
* Index: `ix_user_sessions_fingerprint(user_id, fingerprint)`

---

## `service_account_tokens`

Persisted refresh-token metadata for service accounts.

| Column               | Type         | Null | Default     | Notes                                |
| -------------------- | ------------ | ---- | ----------- | ------------------------------------ |
| `id`                 | UUID         | NO   | `uuid_pk()` |                                      |
| `account`            | String(128)  | NO   | —           |                                      |
| `tenant_id`          | UUID         | YES  | —           | (UUID typed; not a FK)               |
| `scope_key`          | String(256)  | NO   | —           |                                      |
| `scopes`             | JSONB/JSON   | NO   | —           | list[str]                            |
| `refresh_token_hash` | Text         | NO   | —           |                                      |
| `refresh_jti`        | String(64)   | NO   | —           | unique via constraint                |
| `signing_kid`        | String(64)   | NO   | —           |                                      |
| `fingerprint`        | String(128)  | YES  | —           |                                      |
| `session_id`         | UUID         | YES  | —           | FK → `user_sessions.id` (`SET NULL`) |
| `issued_at`          | DateTime(tz) | NO   | `UTC_NOW`   |                                      |
| `expires_at`         | DateTime(tz) | NO   | —           |                                      |
| `revoked_at`         | DateTime(tz) | YES  | —           |                                      |
| `revoked_reason`     | String(256)  | YES  | —           |                                      |
| `created_at`         | DateTime(tz) | NO   | `UTC_NOW`   |                                      |
| `updated_at`         | DateTime(tz) | NO   | `UTC_NOW`   | `onupdate=UTC_NOW`                   |

**Constraints**

* PK: `id`
* FK: `session_id` → `user_sessions.id` (SET NULL)
* Unique: `refresh_jti`
* Index: `ix_service_account_tokens_session_id(session_id)`
* Conditional unique index (Postgres): `uq_service_account_tokens_active_service_accounts(account, tenant_id, scope_key)` where `revoked_at IS NULL AND account NOT LIKE 'user:%'`

---

## `user_mfa_methods`

| Column             | Type                    | Null | Default     | Notes              |
| ------------------ | ----------------------- | ---- | ----------- | ------------------ |
| `id`               | UUID                    | NO   | `uuid_pk()` |                    |
| `user_id`          | UUID                    | NO   | —           | FK → `users.id`    |
| `method_type`      | Enum(`mfa_method_type`) | NO   | —           | totp/webauthn      |
| `label`            | String(64)              | YES  | —           |                    |
| `secret_encrypted` | LargeBinary             | YES  | —           |                    |
| `credential_json`  | JSONB/JSON              | YES  | —           |                    |
| `verified_at`      | DateTime(tz)            | YES  | —           |                    |
| `last_used_at`     | DateTime(tz)            | YES  | —           |                    |
| `revoked_at`       | DateTime(tz)            | YES  | —           |                    |
| `revoked_reason`   | String(128)             | YES  | —           |                    |
| `created_at`       | DateTime(tz)            | NO   | `UTC_NOW`   |                    |
| `updated_at`       | DateTime(tz)            | NO   | `UTC_NOW`   | `onupdate=UTC_NOW` |

**Constraints**

* PK: `id`
* FK: `user_id` → `users.id` (CASCADE)
* Unique: (`user_id`, `label`)
* Index: `ix_user_mfa_methods_user_type(user_id, method_type)`

---

## `user_recovery_codes`

| Column       | Type         | Null | Default     | Notes           |
| ------------ | ------------ | ---- | ----------- | --------------- |
| `id`         | UUID         | NO   | `uuid_pk()` |                 |
| `user_id`    | UUID         | NO   | —           | FK → `users.id` |
| `code_hash`  | String(128)  | NO   | —           |                 |
| `used_at`    | DateTime(tz) | YES  | —           |                 |
| `created_at` | DateTime(tz) | NO   | `UTC_NOW`   |                 |

**Constraints**

* PK: `id`
* FK: `user_id` → `users.id` (CASCADE)
* Index: `ix_user_recovery_codes_user(user_id)`
* Index: `ix_user_recovery_codes_used(used_at)`

---

## `user_consents`

| Column            | Type         | Null | Default     | Notes           |
| ----------------- | ------------ | ---- | ----------- | --------------- |
| `id`              | UUID         | NO   | `uuid_pk()` |                 |
| `user_id`         | UUID         | NO   | —           | FK → `users.id` |
| `policy_key`      | String(64)   | NO   | —           |                 |
| `version`         | String(32)   | NO   | —           |                 |
| `accepted_at`     | DateTime(tz) | NO   | `UTC_NOW`   |                 |
| `ip_hash`         | String(128)  | YES  | —           |                 |
| `user_agent_hash` | String(128)  | YES  | —           |                 |
| `created_at`      | DateTime(tz) | NO   | `UTC_NOW`   |                 |

**Constraints**

* PK: `id`
* FK: `user_id` → `users.id` (CASCADE)
* Unique: (`user_id`, `policy_key`, `version`)
* Index: `ix_user_consents_user_policy(user_id, policy_key)`

---

## `user_notification_preferences`

| Column       | Type         | Null | Default     | Notes                     |
| ------------ | ------------ | ---- | ----------- | ------------------------- |
| `id`         | UUID         | NO   | `uuid_pk()` |                           |
| `user_id`    | UUID         | NO   | —           | FK → `users.id`           |
| `tenant_id`  | UUID         | YES  | —           | FK → `tenant_accounts.id` |
| `channel`    | String(16)   | NO   | —           |                           |
| `category`   | String(64)   | NO   | —           |                           |
| `enabled`    | Boolean      | NO   | `True`      |                           |
| `created_at` | DateTime(tz) | NO   | `UTC_NOW`   |                           |
| `updated_at` | DateTime(tz) | NO   | `UTC_NOW`   | `onupdate=UTC_NOW`        |

**Constraints**

* PK: `id`
* FK: `user_id` → `users.id` (CASCADE)
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* Unique: (`user_id`, `tenant_id`, `channel`, `category`)
* Conditional unique index (Postgres/SQLite): `uq_user_notification_preferences_null_tenant(user_id, channel, category)` where `tenant_id IS NULL`
* Index: `ix_user_notification_preferences_user(user_id)`
* Index: `ix_user_notification_preferences_tenant(tenant_id)`

---

## `usage_counters`

| Column          | Type                              | Null | Default     | Notes                        |
| --------------- | --------------------------------- | ---- | ----------- | ---------------------------- |
| `id`            | UUID                              | NO   | `uuid_pk()` |                              |
| `tenant_id`     | UUID                              | NO   | —           | FK → `tenant_accounts.id`    |
| `user_id`       | UUID                              | YES  | —           | FK → `users.id` (`SET NULL`) |
| `period_start`  | Date                              | NO   | —           |                              |
| `granularity`   | Enum(`usage_counter_granularity`) | NO   | —           | day/month                    |
| `input_tokens`  | BigInteger                        | NO   | `0`         |                              |
| `output_tokens` | BigInteger                        | NO   | `0`         |                              |
| `requests`      | BigInteger                        | NO   | `0`         |                              |
| `storage_bytes` | BigInteger                        | NO   | `0`         |                              |
| `created_at`    | DateTime(tz)                      | NO   | `UTC_NOW`   |                              |
| `updated_at`    | DateTime(tz)                      | NO   | `UTC_NOW`   | `onupdate=UTC_NOW`           |

**Constraints**

* PK: `id`
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* FK: `user_id` → `users.id` (SET NULL)
* Unique: (`tenant_id`, `user_id`, `period_start`, `granularity`)
* Conditional unique index (Postgres/SQLite): `uq_usage_counters_tenant_period_null_user(tenant_id, period_start, granularity)` where `user_id IS NULL`
* Index: `ix_usage_counters_tenant_period(tenant_id, period_start)`
* Index: `ix_usage_counters_user_period(user_id, period_start)`

---

## `security_events`

| Column            | Type         | Null | Default     | Notes                                  |
| ----------------- | ------------ | ---- | ----------- | -------------------------------------- |
| `id`              | UUID         | NO   | `uuid_pk()` |                                        |
| `user_id`         | UUID         | YES  | —           | FK → `users.id` (`SET NULL`)           |
| `tenant_id`       | UUID         | YES  | —           | FK → `tenant_accounts.id` (`SET NULL`) |
| `event_type`      | String(32)   | NO   | —           |                                        |
| `source`          | String(32)   | YES  | —           |                                        |
| `ip_hash`         | String(128)  | YES  | —           |                                        |
| `user_agent_hash` | String(128)  | YES  | —           |                                        |
| `request_id`      | String(128)  | YES  | —           |                                        |
| `metadata_json`   | JSONB/JSON   | YES  | —           |                                        |
| `created_at`      | DateTime(tz) | NO   | `UTC_NOW`   |                                        |

**Constraints**

* PK: `id`
* FK: `user_id` → `users.id` (SET NULL)
* FK: `tenant_id` → `tenant_accounts.id` (SET NULL)
* Index: `ix_security_events_user_created(user_id, created_at)`
* Index: `ix_security_events_tenant_created(tenant_id, created_at)`
* Index: `ix_security_events_type(event_type)`

---

## Activity (from `activity/models.py`)

## `activity_events`

| Column        | Type         | Null | Default     | Notes                       |
| ------------- | ------------ | ---- | ----------- | --------------------------- |
| `id`          | UUID         | NO   | `uuid_pk()` |                             |
| `tenant_id`   | UUID         | NO   | —           | FK → `tenant_accounts.id`   |
| `action`      | String(96)   | NO   | —           |                             |
| `created_at`  | DateTime(tz) | NO   | `UTC_NOW`   |                             |
| `actor_id`    | UUID         | YES  | —           |                             |
| `actor_type`  | String(16)   | YES  | —           |                             |
| `actor_role`  | String(32)   | YES  | —           |                             |
| `object_type` | String(64)   | YES  | —           |                             |
| `object_id`   | String(128)  | YES  | —           |                             |
| `object_name` | String(256)  | YES  | —           |                             |
| `status`      | String(16)   | NO   | `"success"` |                             |
| `source`      | String(32)   | YES  | —           |                             |
| `request_id`  | String(128)  | YES  | —           |                             |
| `ip_hash`     | String(128)  | YES  | —           |                             |
| `user_agent`  | String(512)  | YES  | —           |                             |
| `metadata`    | JSON         | YES  | —           | ORM attr is `metadata_json` |

**Constraints**

* PK: `id`
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* Index: `ix_activity_events_tenant_created(tenant_id, created_at)`
* Index: `ix_activity_events_tenant_action(tenant_id, action)`
* Index: `ix_activity_events_object(tenant_id, object_type, object_id)`
* Index: `ix_activity_events_request(request_id)`

---

## `activity_event_receipts`

| Column       | Type         | Null | Default     | Notes                     |
| ------------ | ------------ | ---- | ----------- | ------------------------- |
| `id`         | UUID         | NO   | `uuid_pk()` |                           |
| `tenant_id`  | UUID         | NO   | —           | FK → `tenant_accounts.id` |
| `user_id`    | UUID         | NO   | —           | FK → `users.id`           |
| `event_id`   | UUID         | NO   | —           | FK → `activity_events.id` |
| `status`     | String(16)   | NO   | —           |                           |
| `created_at` | DateTime(tz) | NO   | `UTC_NOW`   |                           |
| `updated_at` | DateTime(tz) | NO   | `UTC_NOW`   |                           |

**Constraints**

* PK: `id`
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* FK: `user_id` → `users.id` (CASCADE)
* FK: `event_id` → `activity_events.id` (CASCADE)
* Unique: (`tenant_id`, `user_id`, `event_id`)
* Index: `ix_activity_receipts_user_status(tenant_id, user_id, status)`

---

## `activity_last_seen`

| Column                 | Type         | Null | Default     | Notes                     |
| ---------------------- | ------------ | ---- | ----------- | ------------------------- |
| `id`                   | UUID         | NO   | `uuid_pk()` |                           |
| `tenant_id`            | UUID         | NO   | —           | FK → `tenant_accounts.id` |
| `user_id`              | UUID         | NO   | —           | FK → `users.id`           |
| `last_seen_created_at` | DateTime(tz) | NO   | `UTC_NOW`   |                           |
| `last_seen_event_id`   | UUID         | YES  | —           | (no FK)                   |
| `updated_at`           | DateTime(tz) | NO   | `UTC_NOW`   |                           |

**Constraints**

* PK: `id`
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* FK: `user_id` → `users.id` (CASCADE)
* Unique: (`tenant_id`, `user_id`)
* Index: `ix_activity_last_seen_user(tenant_id, user_id)`

---

## Conversations (from `conversations/models.py`)

## `agent_conversations`

| Column                         | Type         | Null | Default     | Notes                        |
| ------------------------------ | ------------ | ---- | ----------- | ---------------------------- |
| `id`                           | UUID         | NO   | `uuid_pk()` |                              |
| `conversation_key`             | String(255)  | NO   | —           | unique via constraint        |
| `tenant_id`                    | UUID         | NO   | —           | FK → `tenant_accounts.id`    |
| `user_id`                      | UUID         | YES  | —           | FK → `users.id` (`SET NULL`) |
| `agent_entrypoint`             | String(64)   | NO   | —           |                              |
| `active_agent`                 | String(64)   | YES  | —           |                              |
| `status`                       | String(16)   | NO   | `"active"`  |                              |
| `message_count`                | Integer      | NO   | `0`         |                              |
| `total_tokens_prompt`          | Integer      | NO   | `0`         |                              |
| `total_tokens_completion`      | Integer      | NO   | `0`         |                              |
| `reasoning_tokens`             | Integer      | NO   | `0`         |                              |
| `total_cached_input_tokens`    | Integer      | NO   | `0`         |                              |
| `total_requests`               | Integer      | NO   | `0`         |                              |
| `provider`                     | String(32)   | YES  | —           |                              |
| `provider_conversation_id`     | String(128)  | YES  | —           | unique                       |
| `handoff_count`                | Integer      | NO   | `0`         |                              |
| `source_channel`               | String(32)   | YES  | —           |                              |
| `topic_hint`                   | String(256)  | YES  | —           |                              |
| `display_name`                 | String(128)  | YES  | —           |                              |
| `title_generated_at`           | DateTime(tz) | YES  | —           |                              |
| `memory_strategy`              | String(16)   | YES  | —           |                              |
| `memory_max_turns`             | Integer      | YES  | —           |                              |
| `memory_keep_last_turns`       | Integer      | YES  | —           |                              |
| `memory_compact_trigger_turns` | Integer      | YES  | —           |                              |
| `memory_compact_keep`          | Integer      | YES  | —           |                              |
| `memory_clear_tool_inputs`     | Boolean      | YES  | —           |                              |
| `memory_injection`             | Boolean      | YES  | —           |                              |
| `last_message_at`              | DateTime(tz) | YES  | —           |                              |
| `last_run_id`                  | String(64)   | YES  | —           |                              |
| `client_version`               | String(32)   | YES  | —           |                              |
| `sdk_session_id`               | String(255)  | YES  | —           |                              |
| `session_cursor`               | String(128)  | YES  | —           |                              |
| `last_session_sync_at`         | DateTime(tz) | YES  | —           |                              |
| `created_at`                   | DateTime(tz) | NO   | `UTC_NOW`   |                              |
| `updated_at`                   | DateTime(tz) | NO   | `UTC_NOW`   |                              |

**Constraints**

* PK: `id`
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* FK: `user_id` → `users.id` (SET NULL)
* Unique: `conversation_key`
* Unique: `provider_conversation_id`
* Index: `ix_agent_conversations_tenant_updated(tenant_id, updated_at)`
* Index: `ix_agent_conversations_tenant_status(tenant_id, status)`

---

## `agent_messages`

| Column                   | Type                | Null | Default   | Notes                                     |
| ------------------------ | ------------------- | ---- | --------- | ----------------------------------------- |
| `id`                     | INT_PK_TYPE         | NO   | autoinc   |                                           |
| `conversation_id`        | UUID                | NO   | —         | FK → `agent_conversations.id`             |
| `segment_id`             | UUID                | NO   | —         | FK → `conversation_ledger_segments.id`    |
| `position`               | Integer             | NO   | —         | unique per conversation via constraint    |
| `role`                   | String(16)          | NO   | —         | user/assistant/system                     |
| `agent_type`             | String(64)          | YES  | —         |                                           |
| `content`                | JSONB/JSON          | NO   | —         |                                           |
| `attachments`            | JSONB/JSON          | YES  | `list`    |                                           |
| `tool_name`              | String(128)         | YES  | —         |                                           |
| `tool_call_id`           | String(64)          | YES  | —         |                                           |
| `token_count_prompt`     | Integer             | YES  | —         |                                           |
| `token_count_completion` | Integer             | YES  | —         |                                           |
| `reasoning_tokens`       | Integer             | YES  | —         |                                           |
| `latency_ms`             | Integer             | YES  | —         |                                           |
| `content_checksum`       | String(32)          | YES  | —         |                                           |
| `run_id`                 | String(64)          | YES  | —         |                                           |
| `text_tsv`               | TSVECTOR (computed) | YES  | computed  | PG computed expression; omitted on SQLite |
| `created_at`             | DateTime(tz)        | NO   | `UTC_NOW` |                                           |

**Constraints**

* PK: `id`
* FK: `conversation_id` → `agent_conversations.id` (CASCADE)
* FK: `segment_id` → `conversation_ledger_segments.id` (CASCADE)
* Unique: (`conversation_id`, `position`)
* Index: `ix_agent_messages_conversation_created(conversation_id, created_at)`

---

## `conversation_summaries`

| Column                  | Type         | Null | Default   | Notes                         |
| ----------------------- | ------------ | ---- | --------- | ----------------------------- |
| `id`                    | INT_PK_TYPE  | NO   | autoinc   |                               |
| `tenant_id`             | UUID         | NO   | —         |                               |
| `conversation_id`       | UUID         | NO   | —         | FK → `agent_conversations.id` |
| `agent_key`             | String(64)   | YES  | —         |                               |
| `summary_text`          | Text         | NO   | —         |                               |
| `summary_model`         | String(64)   | YES  | —         |                               |
| `summary_length_tokens` | Integer      | YES  | —         |                               |
| `expires_at`            | DateTime(tz) | YES  | —         |                               |
| `version`               | String(32)   | YES  | —         |                               |
| `created_at`            | DateTime(tz) | NO   | `UTC_NOW` |                               |

**Constraints**

* PK: `id`
* FK: `conversation_id` → `agent_conversations.id` (CASCADE)

---

## `agent_run_events`

| Column            | Type         | Null | Default   | Notes                                  |
| ----------------- | ------------ | ---- | --------- | -------------------------------------- |
| `id`              | INT_PK_TYPE  | NO   | autoinc   |                                        |
| `conversation_id` | UUID         | NO   | —         | FK → `agent_conversations.id`          |
| `workflow_run_id` | String(64)   | YES  | —         | FK → `workflow_runs.id` (`SET NULL`)   |
| `sequence_no`     | Integer      | NO   | —         | unique per conversation via constraint |
| `response_id`     | String(128)  | YES  | —         |                                        |
| `run_item_type`   | String(64)   | NO   | —         |                                        |
| `run_item_name`   | String(128)  | YES  | —         |                                        |
| `role`            | String(16)   | YES  | —         |                                        |
| `agent`           | String(64)   | YES  | —         |                                        |
| `tool_call_id`    | String(128)  | YES  | —         |                                        |
| `tool_name`       | String(128)  | YES  | —         |                                        |
| `model`           | String(64)   | YES  | —         |                                        |
| `content_text`    | String       | YES  | —         |                                        |
| `reasoning_text`  | String       | YES  | —         |                                        |
| `call_arguments`  | JSONB/JSON   | YES  | —         |                                        |
| `call_output`     | JSONB/JSON   | YES  | —         |                                        |
| `attachments`     | JSONB/JSON   | YES  | —         |                                        |
| `created_at`      | DateTime(tz) | NO   | `UTC_NOW` |                                        |
| `ingested_at`     | DateTime(tz) | NO   | `UTC_NOW` |                                        |

**Constraints**

* PK: `id`
* FK: `conversation_id` → `agent_conversations.id` (CASCADE)
* FK: `workflow_run_id` → `workflow_runs.id` (SET NULL)
* Unique: (`conversation_id`, `sequence_no`)
* Index: `ix_agent_run_events_conv_seq(conversation_id, sequence_no)`
* Index: `ix_agent_run_events_toolcall(tool_call_id)`
* Index: `ix_agent_run_events_conv_type_seq(conversation_id, run_item_type, sequence_no)`
* Index: `ix_agent_run_events_workflow_run(workflow_run_id)`
* Index: `ix_agent_run_events_workflow_run_seq(workflow_run_id, sequence_no)`

---

## `agent_run_usage`

| Column                    | Type         | Null | Default   | Notes                         |
| ------------------------- | ------------ | ---- | --------- | ----------------------------- |
| `id`                      | INT_PK_TYPE  | NO   | autoinc   |                               |
| `tenant_id`               | UUID         | NO   | —         |                               |
| `conversation_id`         | UUID         | NO   | —         | FK → `agent_conversations.id` |
| `response_id`             | String(128)  | YES  | —         | unique via constraint         |
| `run_id`                  | String(64)   | YES  | —         |                               |
| `agent_key`               | String(64)   | YES  | —         |                               |
| `provider`                | String(32)   | YES  | —         |                               |
| `requests`                | Integer      | YES  | —         |                               |
| `input_tokens`            | Integer      | YES  | —         |                               |
| `output_tokens`           | Integer      | YES  | —         |                               |
| `total_tokens`            | Integer      | YES  | —         |                               |
| `cached_input_tokens`     | Integer      | YES  | —         |                               |
| `reasoning_output_tokens` | Integer      | YES  | —         |                               |
| `request_usage_entries`   | JSONB/JSON   | YES  | —         | list[dict]                    |
| `created_at`              | DateTime(tz) | NO   | `UTC_NOW` |                               |

**Constraints**

* PK: `id`
* FK: `conversation_id` → `agent_conversations.id` (CASCADE)
* Unique: `response_id`
* Index: `ix_agent_run_usage_conversation_created(conversation_id, created_at)`
* Index: `ix_agent_run_usage_tenant_created(tenant_id, created_at)`
* Index: `ix_agent_run_usage_response(response_id)`

---

## Conversation Ledger (from `conversations/ledger_models.py`)

## `conversation_ledger_segments`

| Column                             | Type         | Null | Default     | Notes                                               |
| ---------------------------------- | ------------ | ---- | ----------- | --------------------------------------------------- |
| `id`                               | UUID         | NO   | `uuid_pk()` |                                                     |
| `tenant_id`                        | UUID         | NO   | —           | FK → `tenant_accounts.id`                           |
| `conversation_id`                  | UUID         | NO   | —           | FK → `agent_conversations.id`                       |
| `segment_index`                    | Integer      | NO   | —           |                                                     |
| `parent_segment_id`                | UUID         | YES  | —           | FK → `conversation_ledger_segments.id` (`SET NULL`) |
| `visible_through_event_id`         | INT_PK_TYPE  | YES  | —           | no FK by design                                     |
| `visible_through_message_position` | Integer      | YES  | —           |                                                     |
| `truncated_at`                     | DateTime(tz) | YES  | —           |                                                     |
| `created_at`                       | DateTime(tz) | NO   | `UTC_NOW`   |                                                     |
| `updated_at`                       | DateTime(tz) | NO   | `UTC_NOW`   | `onupdate=UTC_NOW`                                  |

**Constraints**

* PK: `id`
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* FK: `conversation_id` → `agent_conversations.id` (CASCADE)
* FK: `parent_segment_id` → `conversation_ledger_segments.id` (SET NULL)
* Unique: (`conversation_id`, `segment_index`)
* Index: `ix_conversation_ledger_segments_conversation_truncated(conversation_id, truncated_at)`

---

## `conversation_ledger_events`

| Column                     | Type         | Null | Default           | Notes                                  |
| -------------------------- | ------------ | ---- | ----------------- | -------------------------------------- |
| `id`                       | INT_PK_TYPE  | NO   | autoinc           |                                        |
| `tenant_id`                | UUID         | NO   | —                 | FK → `tenant_accounts.id`              |
| `conversation_id`          | UUID         | NO   | —                 | FK → `agent_conversations.id`          |
| `segment_id`               | UUID         | NO   | —                 | FK → `conversation_ledger_segments.id` |
| `schema_version`           | String(32)   | NO   | `"public_sse_v1"` |                                        |
| `kind`                     | String(64)   | NO   | —                 |                                        |
| `stream_id`                | String(255)  | NO   | —                 |                                        |
| `event_id`                 | Integer      | NO   | —                 |                                        |
| `server_timestamp`         | DateTime(tz) | NO   | —                 |                                        |
| `response_id`              | String(128)  | YES  | —                 |                                        |
| `agent`                    | String(64)   | YES  | —                 |                                        |
| `workflow_run_id`          | String(64)   | YES  | —                 |                                        |
| `provider_sequence_number` | Integer      | YES  | —                 |                                        |
| `output_index`             | Integer      | YES  | —                 |                                        |
| `item_id`                  | String(255)  | YES  | —                 |                                        |
| `content_index`            | Integer      | YES  | —                 |                                        |
| `tool_call_id`             | String(255)  | YES  | —                 |                                        |
| `payload_size_bytes`       | BigInteger   | YES  | —                 |                                        |
| `payload_json`             | JSONB/JSON   | YES  | —                 | `JSONBCompat`                          |
| `payload_object_id`        | UUID         | YES  | —                 | FK → `storage_objects.id` (`SET NULL`) |
| `ingested_at`              | DateTime(tz) | NO   | `UTC_NOW`         |                                        |

**Constraints**

* PK: `id`
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* FK: `conversation_id` → `agent_conversations.id` (CASCADE)
* FK: `segment_id` → `conversation_ledger_segments.id` (CASCADE)
* FK: `payload_object_id` → `storage_objects.id` (SET NULL)
* Unique: (`conversation_id`, `stream_id`, `event_id`)
* Check: `payload_json IS NOT NULL OR payload_object_id IS NOT NULL`
* Index: `ix_conversation_ledger_events_tenant_conversation_id_id(tenant_id, conversation_id, id)`
* Index: `ix_conversation_ledger_events_tool_call_id(tool_call_id)`
* Index: `ix_conversation_ledger_events_item_id(item_id)`

---

## `conversation_run_queue_items`

| Column               | Type         | Null | Default    | Notes                                               |
| -------------------- | ------------ | ---- | ---------- | --------------------------------------------------- |
| `id`                 | INT_PK_TYPE  | NO   | autoinc    |                                                     |
| `tenant_id`          | UUID         | NO   | —          | FK → `tenant_accounts.id`                           |
| `conversation_id`    | UUID         | NO   | —          | FK → `agent_conversations.id`                       |
| `segment_id`         | UUID         | YES  | —          | FK → `conversation_ledger_segments.id` (`SET NULL`) |
| `created_by_user_id` | UUID         | YES  | —          | FK → `users.id` (`SET NULL`)                        |
| `status`             | String(16)   | NO   | `"queued"` |                                                     |
| `attempt_count`      | Integer      | NO   | `0`        |                                                     |
| `payload_json`       | JSONB/JSON   | NO   | —          |                                                     |
| `error_json`         | JSONB/JSON   | YES  | —          |                                                     |
| `created_at`         | DateTime(tz) | NO   | `UTC_NOW`  |                                                     |
| `started_at`         | DateTime(tz) | YES  | —          |                                                     |
| `completed_at`       | DateTime(tz) | YES  | —          |                                                     |
| `cancelled_at`       | DateTime(tz) | YES  | —          |                                                     |

**Constraints**

* PK: `id`
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* FK: `conversation_id` → `agent_conversations.id` (CASCADE)
* FK: `segment_id` → `conversation_ledger_segments.id` (SET NULL)
* FK: `created_by_user_id` → `users.id` (SET NULL)
* Index: `ix_conversation_run_queue_items_conversation_status_id(conversation_id, status, id)`
* Index: `ix_conversation_run_queue_items_tenant_conversation_status_id(tenant_id, conversation_id, status, id)`

---

## Billing (from `billing/models.py`)

## `billing_plans`

| Column            | Type         | Null | Default     | Notes                 |
| ----------------- | ------------ | ---- | ----------- | --------------------- |
| `id`              | UUID         | NO   | `uuid_pk()` |                       |
| `code`            | String(64)   | NO   | —           | unique via constraint |
| `name`            | String(128)  | NO   | —           |                       |
| `interval`        | String(16)   | NO   | `"monthly"` |                       |
| `interval_count`  | Integer      | NO   | `1`         |                       |
| `price_cents`     | Integer      | NO   | —           |                       |
| `currency`        | String(3)    | NO   | `"USD"`     |                       |
| `trial_days`      | Integer      | YES  | —           |                       |
| `seat_included`   | Integer      | YES  | —           |                       |
| `feature_toggles` | JSONB/JSON   | YES  | —           |                       |
| `is_active`       | Boolean      | NO   | `True`      |                       |
| `created_at`      | DateTime(tz) | NO   | `UTC_NOW`   |                       |
| `updated_at`      | DateTime(tz) | NO   | `UTC_NOW`   |                       |

**Constraints**

* PK: `id`
* Unique: `code`

---

## `plan_features`

| Column         | Type         | Null | Default   | Notes                   |
| -------------- | ------------ | ---- | --------- | ----------------------- |
| `id`           | INT_PK_TYPE  | NO   | autoinc   |                         |
| `plan_id`      | UUID         | NO   | —         | FK → `billing_plans.id` |
| `feature_key`  | String(64)   | NO   | —         |                         |
| `display_name` | String(128)  | YES  | —         |                         |
| `description`  | Text         | YES  | —         |                         |
| `hard_limit`   | Integer      | YES  | —         |                         |
| `soft_limit`   | Integer      | YES  | —         |                         |
| `is_metered`   | Boolean      | NO   | `False`   |                         |
| `created_at`   | DateTime(tz) | NO   | `UTC_NOW` |                         |

**Constraints**

* PK: `id`
* FK: `plan_id` → `billing_plans.id` (CASCADE)
* Unique: (`plan_id`, `feature_key`)

---

## `tenant_subscriptions`

| Column                      | Type         | Null | Default     | Notes                                |
| --------------------------- | ------------ | ---- | ----------- | ------------------------------------ |
| `id`                        | UUID         | NO   | `uuid_pk()` |                                      |
| `tenant_id`                 | UUID         | NO   | —           | FK → `tenant_accounts.id`            |
| `plan_id`                   | UUID         | NO   | —           | FK → `billing_plans.id` (`RESTRICT`) |
| `status`                    | String(24)   | NO   | `"active"`  |                                      |
| `auto_renew`                | Boolean      | NO   | `True`      |                                      |
| `billing_email`             | String(256)  | YES  | —           |                                      |
| `processor`                 | String(32)   | YES  | —           |                                      |
| `processor_customer_id`     | String(128)  | YES  | —           |                                      |
| `processor_subscription_id` | String(128)  | YES  | —           |                                      |
| `starts_at`                 | DateTime(tz) | NO   | `UTC_NOW`   |                                      |
| `current_period_start`      | DateTime(tz) | YES  | —           |                                      |
| `current_period_end`        | DateTime(tz) | YES  | —           |                                      |
| `trial_ends_at`             | DateTime(tz) | YES  | —           |                                      |
| `cancel_at`                 | DateTime(tz) | YES  | —           |                                      |
| `seat_count`                | Integer      | YES  | —           |                                      |
| `metadata_json`             | JSONB/JSON   | YES  | —           |                                      |
| `created_at`                | DateTime(tz) | NO   | `UTC_NOW`   |                                      |
| `updated_at`                | DateTime(tz) | NO   | `UTC_NOW`   |                                      |

**Constraints**

* PK: `id`
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* FK: `plan_id` → `billing_plans.id` (RESTRICT)
* Index: `ix_tenant_subscriptions_tenant_status(tenant_id, status)`

---

## `subscription_invoices`

| Column                | Type         | Null | Default     | Notes                          |
| --------------------- | ------------ | ---- | ----------- | ------------------------------ |
| `id`                  | UUID         | NO   | `uuid_pk()` |                                |
| `subscription_id`     | UUID         | NO   | —           | FK → `tenant_subscriptions.id` |
| `period_start`        | DateTime(tz) | NO   | —           |                                |
| `period_end`          | DateTime(tz) | NO   | —           |                                |
| `amount_cents`        | Integer      | NO   | —           |                                |
| `currency`            | String(3)    | NO   | `"USD"`     |                                |
| `status`              | String(16)   | NO   | `"draft"`   |                                |
| `external_invoice_id` | String(128)  | YES  | —           |                                |
| `hosted_invoice_url`  | String(256)  | YES  | —           |                                |
| `created_at`          | DateTime(tz) | NO   | `UTC_NOW`   |                                |

**Constraints**

* PK: `id`
* FK: `subscription_id` → `tenant_subscriptions.id` (CASCADE)
* Index: `ix_subscription_invoices_subscription_period(subscription_id, period_start)`

---

## `subscription_usage`

| Column              | Type         | Null | Default     | Notes                          |
| ------------------- | ------------ | ---- | ----------- | ------------------------------ |
| `id`                | UUID         | NO   | `uuid_pk()` |                                |
| `subscription_id`   | UUID         | NO   | —           | FK → `tenant_subscriptions.id` |
| `feature_key`       | String(64)   | NO   | —           |                                |
| `unit`              | String(32)   | NO   | —           |                                |
| `period_start`      | DateTime(tz) | NO   | —           |                                |
| `period_end`        | DateTime(tz) | NO   | —           |                                |
| `quantity`          | Integer      | NO   | —           |                                |
| `reported_at`       | DateTime(tz) | NO   | `UTC_NOW`   |                                |
| `external_event_id` | String(128)  | YES  | —           |                                |

**Constraints**

* PK: `id`
* FK: `subscription_id` → `tenant_subscriptions.id` (CASCADE)
* Unique: (`subscription_id`, `feature_key`, `period_start`)

---

## Stripe (from `stripe/models.py`)

## `stripe_events`

| Column                | Type         | Null | Default      | Notes          |
| --------------------- | ------------ | ---- | ------------ | -------------- |
| `id`                  | UUID         | NO   | `uuid_pk()`  |                |
| `stripe_event_id`     | String(64)   | NO   | —            | unique         |
| `event_type`          | String(128)  | NO   | —            |                |
| `payload`             | JSONB/JSON   | NO   | —            |                |
| `tenant_hint`         | String(64)   | YES  | —            |                |
| `stripe_created_at`   | DateTime(tz) | YES  | —            |                |
| `received_at`         | DateTime(tz) | NO   | `UTC_NOW`    |                |
| `processed_at`        | DateTime(tz) | YES  | —            |                |
| `processing_outcome`  | String(32)   | NO   | `"received"` | values in code |
| `processing_error`    | Text         | YES  | —            |                |
| `processing_attempts` | Integer      | NO   | `0`          |                |

**Constraints**

* PK: `id`
* Unique: `stripe_event_id`
* Index: `ix_stripe_events_type(event_type)`
* Index: `ix_stripe_events_status(processing_outcome)`

---

## `stripe_event_dispatch`

| Column            | Type         | Null | Default     | Notes                   |
| ----------------- | ------------ | ---- | ----------- | ----------------------- |
| `id`              | UUID         | NO   | `uuid_pk()` |                         |
| `stripe_event_id` | UUID         | NO   | —           | FK → `stripe_events.id` |
| `handler`         | String(64)   | NO   | —           |                         |
| `status`          | String(32)   | NO   | `"pending"` | values in code          |
| `attempts`        | Integer      | NO   | `0`         |                         |
| `last_attempt_at` | DateTime(tz) | YES  | —           |                         |
| `next_retry_at`   | DateTime(tz) | YES  | —           |                         |
| `last_error`      | Text         | YES  | —           |                         |
| `created_at`      | DateTime(tz) | NO   | `UTC_NOW`   |                         |
| `updated_at`      | DateTime(tz) | NO   | `UTC_NOW`   | `onupdate=UTC_NOW`      |

**Constraints**

* PK: `id`
* FK: `stripe_event_id` → `stripe_events.id` (CASCADE)
* Unique: (`stripe_event_id`, `handler`)
* Index: `ix_stripe_event_dispatch_handler_status(handler, status, next_retry_at)`

---

## Containers (from `containers/models.py`)

## `containers`

| Column           | Type         | Null | Default     | Notes                        |
| ---------------- | ------------ | ---- | ----------- | ---------------------------- |
| `id`             | UUID         | NO   | `uuid_pk()` |                              |
| `openai_id`      | String(64)   | NO   | —           | unique                       |
| `tenant_id`      | UUID         | NO   | —           | FK → `tenant_accounts.id`    |
| `owner_user_id`  | UUID         | YES  | —           | FK → `users.id` (`SET NULL`) |
| `name`           | String(128)  | NO   | —           |                              |
| `memory_limit`   | String(8)    | NO   | `"1g"`      |                              |
| `status`         | String(32)   | NO   | `"running"` |                              |
| `expires_after`  | JSONB/JSON   | YES  | —           |                              |
| `last_active_at` | DateTime(tz) | YES  | —           |                              |
| `metadata_json`  | JSONB/JSON   | NO   | `dict`      |                              |
| `created_at`     | DateTime(tz) | NO   | `UTC_NOW`   |                              |
| `updated_at`     | DateTime(tz) | NO   | `UTC_NOW`   | `onupdate=UTC_NOW`           |
| `deleted_at`     | DateTime(tz) | YES  | —           |                              |

**Constraints**

* PK: `id`
* Unique: `openai_id`
* Unique: (`tenant_id`, `name`, `deleted_at`)
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* FK: `owner_user_id` → `users.id` (SET NULL)
* Index: `ix_containers_tenant_status(tenant_id, status)`
* Index: `ix_containers_tenant_created(tenant_id, created_at)`

---

## `agent_containers`

| Column         | Type       | Null | Default | Notes                                 |
| -------------- | ---------- | ---- | ------- | ------------------------------------- |
| `agent_key`    | String(64) | NO   | —       | part of composite PK                  |
| `container_id` | UUID       | NO   | —       | FK → `containers.id`, part of PK      |
| `tenant_id`    | UUID       | NO   | —       | FK → `tenant_accounts.id`, part of PK |

**Constraints**

* PK (composite): (`agent_key`, `container_id`, `tenant_id`)
* FK: `container_id` → `containers.id` (CASCADE)
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)

---

## Storage (from `storage/models.py`)

## `storage_buckets`

| Column        | Type         | Null | Default     | Notes                     |
| ------------- | ------------ | ---- | ----------- | ------------------------- |
| `id`          | UUID         | NO   | `uuid_pk()` |                           |
| `tenant_id`   | UUID         | NO   | —           | FK → `tenant_accounts.id` |
| `provider`    | String(16)   | NO   | —           |                           |
| `bucket_name` | String(128)  | NO   | —           |                           |
| `region`      | String(64)   | YES  | —           |                           |
| `prefix`      | String(128)  | YES  | —           |                           |
| `is_default`  | Boolean      | NO   | `True`      |                           |
| `status`      | String(16)   | NO   | `"ready"`   |                           |
| `created_at`  | DateTime(tz) | NO   | `UTC_NOW`   |                           |
| `updated_at`  | DateTime(tz) | NO   | `UTC_NOW`   | `onupdate=UTC_NOW`        |
| `deleted_at`  | DateTime(tz) | YES  | —           |                           |

**Constraints**

* PK: `id`
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* Unique: (`tenant_id`, `bucket_name`)
* Index: `ix_storage_buckets_tenant_provider(tenant_id, provider)`

---

## `storage_objects`

| Column               | Type         | Null | Default     | Notes                                      |
| -------------------- | ------------ | ---- | ----------- | ------------------------------------------ |
| `id`                 | UUID         | NO   | `uuid_pk()` |                                            |
| `tenant_id`          | UUID         | NO   | —           | FK → `tenant_accounts.id`                  |
| `bucket_id`          | UUID         | NO   | —           | FK → `storage_buckets.id`                  |
| `object_key`         | String(512)  | NO   | —           |                                            |
| `filename`           | String(256)  | NO   | —           |                                            |
| `mime_type`          | String(128)  | YES  | —           |                                            |
| `size_bytes`         | BigInteger   | YES  | —           |                                            |
| `checksum_sha256`    | String(64)   | YES  | —           |                                            |
| `status`             | String(16)   | NO   | `"pending"` |                                            |
| `created_by_user_id` | UUID         | YES  | —           | FK → `users.id` (`SET NULL`)               |
| `agent_key`          | String(64)   | YES  | —           |                                            |
| `conversation_id`    | UUID         | YES  | —           | FK → `agent_conversations.id` (`SET NULL`) |
| `metadata_json`      | JSONB/JSON   | NO   | `dict`      |                                            |
| `expires_at`         | DateTime(tz) | YES  | —           |                                            |
| `deleted_at`         | DateTime(tz) | YES  | —           |                                            |
| `created_at`         | DateTime(tz) | NO   | `UTC_NOW`   |                                            |
| `updated_at`         | DateTime(tz) | NO   | `UTC_NOW`   | `onupdate=UTC_NOW`                         |

**Constraints**

* PK: `id`
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* FK: `bucket_id` → `storage_buckets.id` (CASCADE)
* FK: `created_by_user_id` → `users.id` (SET NULL)
* FK: `conversation_id` → `agent_conversations.id` (SET NULL)
* Unique: (`bucket_id`, `object_key`)
* Index: `ix_storage_objects_tenant_status(tenant_id, status)`
* Index: `ix_storage_objects_conversation(conversation_id)`

---

## Vector Stores (from `vector_stores/models.py`)

## `vector_stores`

| Column           | Type         | Null | Default      | Notes                            |
| ---------------- | ------------ | ---- | ------------ | -------------------------------- |
| `id`             | UUID         | NO   | `uuid_pk()`  |                                  |
| `openai_id`      | String(64)   | NO   | —            | unique                           |
| `tenant_id`      | UUID         | NO   | —            | FK → `tenant_accounts.id`        |
| `owner_user_id`  | UUID         | YES  | —            | FK → `users.id` (`SET NULL`)     |
| `name`           | String(128)  | NO   | —            | unique per tenant via constraint |
| `description`    | Text         | YES  | —            |                                  |
| `status`         | String(16)   | NO   | `"creating"` |                                  |
| `usage_bytes`    | Integer      | NO   | `0`          |                                  |
| `expires_after`  | JSONB/JSON   | YES  | —            |                                  |
| `expires_at`     | DateTime(tz) | YES  | —            |                                  |
| `last_active_at` | DateTime(tz) | YES  | —            |                                  |
| `metadata_json`  | JSONB/JSON   | NO   | `dict`       |                                  |
| `created_at`     | DateTime(tz) | NO   | `UTC_NOW`    |                                  |
| `updated_at`     | DateTime(tz) | NO   | `UTC_NOW`    | `onupdate=UTC_NOW`               |
| `deleted_at`     | DateTime(tz) | YES  | —            |                                  |

**Constraints**

* PK: `id`
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* FK: `owner_user_id` → `users.id` (SET NULL)
* Unique: `openai_id`
* Unique: (`tenant_id`, `name`)
* Index: `ix_vector_stores_tenant_status(tenant_id, status)`
* Index: `ix_vector_stores_tenant_created(tenant_id, created_at)`

---

## `vector_store_files`

| Column            | Type         | Null | Default      | Notes                   |
| ----------------- | ------------ | ---- | ------------ | ----------------------- |
| `id`              | UUID         | NO   | `uuid_pk()`  |                         |
| `openai_file_id`  | String(64)   | NO   | —            |                         |
| `vector_store_id` | UUID         | NO   | —            | FK → `vector_stores.id` |
| `filename`        | String(256)  | NO   | —            |                         |
| `mime_type`       | String(128)  | YES  | —            |                         |
| `size_bytes`      | Integer      | YES  | —            |                         |
| `usage_bytes`     | Integer      | NO   | `0`          |                         |
| `status`          | String(16)   | NO   | `"indexing"` |                         |
| `attributes_json` | JSONB/JSON   | NO   | `dict`       |                         |
| `chunking_json`   | JSONB/JSON   | YES  | —            |                         |
| `last_error`      | Text         | YES  | —            |                         |
| `created_at`      | DateTime(tz) | NO   | `UTC_NOW`    |                         |
| `updated_at`      | DateTime(tz) | NO   | `UTC_NOW`    | `onupdate=UTC_NOW`      |
| `deleted_at`      | DateTime(tz) | YES  | —            |                         |

**Constraints**

* PK: `id`
* FK: `vector_store_id` → `vector_stores.id` (CASCADE)
* Unique: (`vector_store_id`, `openai_file_id`)
* Index: `ix_vector_store_files_store_status(vector_store_id, status)`

---

## `agent_vector_stores`

| Column            | Type       | Null | Default | Notes                                 |
| ----------------- | ---------- | ---- | ------- | ------------------------------------- |
| `agent_key`       | String(64) | NO   | —       | part of composite PK                  |
| `vector_store_id` | UUID       | NO   | —       | FK → `vector_stores.id`, part of PK   |
| `tenant_id`       | UUID       | NO   | —       | FK → `tenant_accounts.id`, part of PK |

**Constraints**

* PK (composite): (`agent_key`, `vector_store_id`, `tenant_id`)
* FK: `vector_store_id` → `vector_stores.id` (CASCADE)
* FK: `tenant_id` → `tenant_accounts.id` (CASCADE)
* Unique: (`tenant_id`, `agent_key`)  *(one store per agent per tenant)*

---

## Status (from `status/models.py`)

## `status_subscriptions`

| Column                        | Type         | Null | Default        | Notes                |
| ----------------------------- | ------------ | ---- | -------------- | -------------------- |
| `id`                          | UUID         | NO   | `uuid.uuid4()` |                      |
| `channel`                     | String(16)   | NO   | —              | SubscriptionChannel  |
| `target_hash`                 | String(128)  | NO   | —              | indexed              |
| `target_masked`               | String(512)  | NO   | —              |                      |
| `target_encrypted`            | LargeBinary  | NO   | —              |                      |
| `severity_filter`             | String(16)   | NO   | —              | SubscriptionSeverity |
| `status`                      | String(32)   | NO   | —              | SubscriptionStatus   |
| `tenant_id`                   | UUID         | YES  | —              | indexed              |
| `metadata_json`               | JSONB/JSON   | NO   | `dict`         |                      |
| `created_by`                  | String(64)   | NO   | —              |                      |
| `verification_token_hash`     | String(128)  | YES  | —              | indexed              |
| `verification_expires_at`     | DateTime(tz) | YES  | —              |                      |
| `challenge_token_hash`        | String(128)  | YES  | —              | indexed              |
| `webhook_secret_encrypted`    | LargeBinary  | YES  | —              |                      |
| `unsubscribe_token_hash`      | String(128)  | YES  | —              | indexed              |
| `unsubscribe_token_encrypted` | LargeBinary  | YES  | —              |                      |
| `revoked_reason`              | Text         | YES  | —              |                      |
| `created_at`                  | DateTime(tz) | NO   | `UTC_NOW`      |                      |
| `updated_at`                  | DateTime(tz) | NO   | `UTC_NOW`      | `onupdate=UTC_NOW`   |
| `revoked_at`                  | DateTime(tz) | YES  | —              |                      |
| `last_challenge_sent_at`      | DateTime(tz) | YES  | —              |                      |

**Constraints**

* PK: `id`
* Index: `target_hash`
* Index: `tenant_id`
* Index: `verification_token_hash`
* Index: `challenge_token_hash`
* Index: `unsubscribe_token_hash`

---

## Workflows (from `workflows/models.py`)

## `workflow_runs`

| Column                    | Type         | Null | Default | Notes                                                             |
| ------------------------- | ------------ | ---- | ------- | ----------------------------------------------------------------- |
| `id`                      | String       | NO   | —       | PK                                                                |
| `workflow_key`            | String       | NO   | —       | indexed                                                           |
| `tenant_id`               | String       | NO   | —       | indexed                                                           |
| `user_id`                 | String       | NO   | —       | indexed                                                           |
| `status`                  | String       | NO   | —       |                                                                   |
| `started_at`              | DateTime(tz) | NO   | —       |                                                                   |
| `ended_at`                | DateTime(tz) | YES  | —       |                                                                   |
| `final_output_text`       | String       | YES  | —       |                                                                   |
| `final_output_structured` | JSONB/JSON   | YES  | —       |                                                                   |
| `trace_id`                | String       | YES  | —       |                                                                   |
| `request_message`         | String       | YES  | —       |                                                                   |
| `conversation_id`         | String(255)  | YES  | —       | FK → `agent_conversations.conversation_key` (`SET NULL`), indexed |
| `metadata`                | JSONB/JSON   | YES  | —       | column name is `metadata`                                         |
| `deleted_at`              | DateTime(tz) | YES  | —       | indexed                                                           |
| `deleted_by`              | String       | YES  | —       |                                                                   |
| `deleted_reason`          | String       | YES  | —       |                                                                   |

**Constraints**

* PK: `id`
* FK: `conversation_id` → `agent_conversations.conversation_key` (SET NULL)

---

## `workflow_run_steps`

| Column                | Type         | Null | Default | Notes                                   |
| --------------------- | ------------ | ---- | ------- | --------------------------------------- |
| `id`                  | String       | NO   | —       | PK                                      |
| `workflow_run_id`     | String       | NO   | —       | indexed (no FK constraint defined here) |
| `sequence_no`         | Integer      | NO   | —       |                                         |
| `step_name`           | String       | NO   | —       |                                         |
| `step_agent`          | String       | NO   | —       |                                         |
| `status`              | String       | NO   | —       |                                         |
| `started_at`          | DateTime(tz) | NO   | —       |                                         |
| `ended_at`            | DateTime(tz) | YES  | —       |                                         |
| `response_id`         | String       | YES  | —       |                                         |
| `response_text`       | String       | YES  | —       |                                         |
| `structured_output`   | JSONB/JSON   | YES  | —       |                                         |
| `raw_payload`         | JSONB/JSON   | YES  | —       |                                         |
| `usage_input_tokens`  | Integer      | YES  | —       |                                         |
| `usage_output_tokens` | Integer      | YES  | —       |                                         |
| `stage_name`          | String       | YES  | —       |                                         |
| `parallel_group`      | String       | YES  | —       |                                         |
| `branch_index`        | Integer      | YES  | —       |                                         |
| `deleted_at`          | DateTime(tz) | YES  | —       | indexed                                 |
| `deleted_by`          | String       | YES  | —       |                                         |
| `deleted_reason`      | String       | YES  | —       |                                         |

**Constraints**

* PK: `id`

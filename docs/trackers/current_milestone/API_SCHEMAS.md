## Endpoint inventory (`/api/v1/...`)

### Activity

* **GET** `/activity` → `ActivityListResponse` ✅
* **GET** `/activity/stream` → SSE (OpenAPI patched to `ActivityEventItem`) ✅ *(router has no response_model)*
* **POST** `/activity/{event_id}/read` → `ReceiptResponse` ✅
* **POST** `/activity/{event_id}/dismiss` → `ReceiptResponse` ✅
* **POST** `/activity/mark-all-read` → `ReceiptResponse` ✅

### Agents

* **GET** `/agents` → `AgentListResponse` ✅
* **GET** `/agents/{agent_name}/status` → `AgentStatus` ✅

### Auth

**Sessions**

* **POST** `/auth/token` → `UserSessionResponse | MfaChallengeResponse` ✅
* **POST** `/auth/refresh` → `UserSessionResponse` ✅
* **POST** `/auth/logout` → `SessionRevocationSuccessResponse` ✅
* **POST** `/auth/logout/all` → `SessionRevocationSuccessResponse` ✅
* **GET** `/auth/sessions` → `UserSessionListResponse` ✅
* **DELETE** `/auth/sessions/{session_id}` → `SessionRevocationSuccessResponse` ✅
* **GET** `/auth/me` → `CurrentUserInfoSuccessResponse` ✅

**Email verification**

* **POST** `/auth/email/send` → `EmailVerificationSendSuccessResponse` ✅
* **POST** `/auth/email/verify` → `SuccessNoDataResponse` ✅

**Passwords**

* **POST** `/auth/password/forgot` → `SuccessNoDataResponse` ✅
* **POST** `/auth/password/confirm` → `SuccessNoDataResponse` ✅
* **POST** `/auth/password/change` → `SuccessNoDataResponse` ✅
* **POST** `/auth/password/reset` → `SuccessNoDataResponse` ✅

**Signup**

* **GET** `/auth/signup-policy` → `SignupAccessPolicyResponse` ✅
* **POST** `/auth/register` → `UserRegisterResponse` ✅
* **POST** `/auth/request-access` → `SignupAccessPolicyResponse` ✅

**Signup requests**

* **GET** `/auth/signup-requests` → `SignupRequestListResponse` ✅
* **POST** `/auth/signup-requests/{request_id}/approve` → `SignupRequestDecisionResponse` ✅
* **POST** `/auth/signup-requests/{request_id}/reject` → `SignupRequestDecisionResponse` ✅

**Invites**

* **GET** `/auth/invites` → `SignupInviteListResponse` ✅
* **POST** `/auth/invites` → `SignupInviteIssueResponse` ✅
* **POST** `/auth/invites/{invite_id}/revoke` → `SignupInviteResponse` ✅

**MFA**

* **GET** `/auth/mfa` → `list[MfaMethodView]` ✅
* **POST** `/auth/mfa/totp/enroll` → `TotpEnrollResponse` ✅
* **POST** `/auth/mfa/totp/verify` → `SuccessNoDataResponse` ✅
* **DELETE** `/auth/mfa/{method_id}` → `SuccessNoDataResponse` ✅
* **POST** `/auth/mfa/recovery/regenerate` → `RecoveryCodesResponse` ✅
* **POST** `/auth/mfa/complete` → `UserSessionResponse` ✅

**Service accounts**

* **POST** `/auth/service-accounts/issue` → `ServiceAccountTokenResponse` ✅
* **POST** `/auth/service-accounts/browser-issue` → `ServiceAccountTokenResponse` ✅
* **GET** `/auth/service-accounts/tokens` → `ServiceAccountTokenListResponse` ✅
* **POST** `/auth/service-accounts/tokens/{jti}/revoke` → `ServiceAccountTokenRevokeSuccessResponse` ✅

### Billing *(only when `enable_billing`)*

* **GET** `/billing/plans` → `list[BillingPlanResponse]` ✅
* **GET** `/billing/tenants/{tenant_id}/subscription` → `TenantSubscriptionResponse` ✅
* **POST** `/billing/tenants/{tenant_id}/subscription` → `TenantSubscriptionResponse` ✅
* **PATCH** `/billing/tenants/{tenant_id}/subscription` → `TenantSubscriptionResponse` ✅
* **POST** `/billing/tenants/{tenant_id}/subscription/cancel` → `TenantSubscriptionResponse` ✅
* **POST** `/billing/tenants/{tenant_id}/usage` → `SuccessNoDataResponse` ✅
* **GET** `/billing/tenants/{tenant_id}/events` → `BillingEventHistoryResponse` ✅
* **GET** `/billing/stream` → SSE (OpenAPI patched to `BillingEventResponse`) ✅ *(router has no response_model)*

### Chat

* **POST** `/chat` → `AgentChatResponse` ✅
* **POST** `/chat/stream` → SSE `StreamingChatEvent` ✅ *(router declares SSE schema)*

### Contact

* **POST** `/contact` → `ContactSubmissionSuccessResponse` ✅

### Containers

* **POST** `/containers` → `ContainerResponse` ✅
* **GET** `/containers` → `ContainerListResponse` ✅
* **GET** `/containers/{container_id}` → `ContainerResponse` ✅
* **DELETE** `/containers/{container_id}` → `204` ✅
* **POST** `/containers/agents/{agent_key}/container` → `204` ✅
* **DELETE** `/containers/agents/{agent_key}/container` → `204` ✅

### Conversations

* **GET** `/conversations` → `ConversationListResponse` ✅
* **GET** `/conversations/search` → `ConversationSearchResponse` ✅
* **GET** `/conversations/{conversation_id}` → `ConversationHistory` ✅
* **GET** `/conversations/{conversation_id}/messages` → `PaginatedMessagesResponse` ✅
* **PATCH** `/conversations/{conversation_id}/memory` → `ConversationMemoryConfigResponse` ✅
* **GET** `/conversations/{conversation_id}/events` → `ConversationEventsResponse` ✅
* **GET** `/conversations/{conversation_id}/stream` → SSE `ConversationMetaEvent` ✅ *(router declares SSE schema)*
* **DELETE** `/conversations/{conversation_id}` → `204` ✅

### Guardrails

* **GET** `/guardrails` → `list[GuardrailSummary]` ✅
* **GET** `/guardrails/presets` → `list[PresetSummary]` ✅
* **GET** `/guardrails/{guardrail_key}` → `GuardrailDetail` ✅
* **GET** `/guardrails/presets/{preset_key}` → `PresetDetail` ✅

### Logs *(only when `enable_frontend_log_ingest`)*

* **POST** `/logs` → `FrontendLogIngestResponse` ✅

### OpenAI files

* **GET** `/openai/files/{file_id}/download` → binary ✅ *(OpenAPI patched)*
* **GET** `/openai/containers/{container_id}/files/{file_id}/download` → binary ✅ *(OpenAPI patched)*

### Status

* **GET** `/status` → `PlatformStatusResponse` ✅
* **GET** `/status/rss` → RSS XML ✅ *(OpenAPI patched)*
* **POST** `/status/subscriptions` → `StatusSubscriptionResponse` ✅
* **POST** `/status/subscriptions/verify` → `StatusSubscriptionResponse` ✅
* **POST** `/status/subscriptions/challenge` → `StatusSubscriptionResponse` ✅
* **GET** `/status/subscriptions` → `StatusSubscriptionListResponse` ✅
* **DELETE** `/status/subscriptions/{subscription_id}` → `204` ✅
* **POST** `/status/incidents/{incident_id}/resend` → `StatusIncidentResendResponse` ✅

### Storage

* **POST** `/storage/objects/upload-url` → `StoragePresignUploadResponse` ✅
* **GET** `/storage/objects` → `StorageObjectListResponse` ✅
* **GET** `/storage/objects/{object_id}/download-url` → `StoragePresignDownloadResponse` ✅
* **DELETE** `/storage/objects/{object_id}` → `204` ✅

### Tenants

* **GET** `/tenants/settings` → `TenantSettingsResponse` ✅
* **PUT** `/tenants/settings` → `TenantSettingsResponse` ✅

### Test fixtures *(only when `use_test_fixtures`)*

* **POST** `/test-fixtures/apply` → `FixtureApplyResult` ✅
* **POST** `/test-fixtures/email-verification-token` → `EmailVerificationTokenResponse` ✅

### Tools

* **GET** `/tools` → `ToolCatalogResponse` ✅

### Usage

* **GET** `/usage` → `list[UsageCounterView]` ✅

### Users

* **POST** `/users/consents` → `SuccessNoDataResponse` ✅
* **GET** `/users/consents` → `list[ConsentView]` ✅
* **PUT** `/users/notification-preferences` → `NotificationPreferenceView` ✅
* **GET** `/users/notification-preferences` → `list[NotificationPreferenceView]` ✅

### Vector stores

* **POST** `/vector-stores` → `VectorStoreResponse` ✅
* **GET** `/vector-stores` → `VectorStoreListResponse` ✅
* **GET** `/vector-stores/{vector_store_id}` → `VectorStoreResponse` ✅
* **DELETE** `/vector-stores/{vector_store_id}` → `204` ✅
* **POST** `/vector-stores/{vector_store_id}/files` → `VectorStoreFileResponse` ✅
* **GET** `/vector-stores/{vector_store_id}/files` → `VectorStoreFileListResponse` ✅
* **GET** `/vector-stores/{vector_store_id}/files/{file_id}` → `VectorStoreFileResponse` ✅
* **DELETE** `/vector-stores/{vector_store_id}/files/{file_id}` → `204` ✅
* **POST** `/vector-stores/{vector_store_id}/search` → `VectorStoreSearchResponse` ✅
* **POST** `/vector-stores/{vector_store_id}/bindings/{agent_key}` → `204` ✅
* **DELETE** `/vector-stores/{vector_store_id}/bindings/{agent_key}` → `204` ✅

### Workflows

* **GET** `/workflows` → `WorkflowListResponse` ✅
* **GET** `/workflows/{workflow_key}` → `WorkflowDescriptorResponse` ✅
* **POST** `/workflows/{workflow_key}/run` → `WorkflowRunResponse` ✅
* **POST** `/workflows/{workflow_key}/run-stream` → SSE `StreamingWorkflowEvent` ✅ *(router declares SSE schema)*
* **GET** `/workflows/runs` → `WorkflowRunListResponse` ✅
* **GET** `/workflows/runs/{run_id}` → `WorkflowRunDetail` ✅
* **POST** `/workflows/runs/{run_id}/cancel` → `WorkflowRunCancelResponse` ✅
* **DELETE** `/workflows/runs/{run_id}` → `204` ✅

---

## What’s still missing / I’d fix next

1. **`POST /api/v1/logs` has no response schema**

* Add `response_model` (either a tiny DTO like `FrontendLogIngestResponse(accepted: bool)` or a `SuccessNoDataResponse` + message).
* Right now clients will infer `object`/`any` for 202 responses.

2. Still “special” endpoints relying on OpenAPI patching (not `response_model`)

* `/activity/stream`, `/billing/stream`, the OpenAI binary downloads, RSS
* This is fine (your patch layer is explicit), just keep it consistent.

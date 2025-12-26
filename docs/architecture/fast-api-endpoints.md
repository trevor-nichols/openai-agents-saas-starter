# API Service

> Source of truth: the generated OpenAPI schema. Regenerate with
> `starter-console api export-openapi --output apps/api-service/.artifacts/openapi.json`
> and consult that artifact (or `/docs` in a running server) for the current list.

# API Endpoints

## health

`GET` `/health`
- Health Check

`GET` `/health/ready`
- Readiness Check

`GET` `/health/storage`
- Storage Health

## default

`POST` `/webhooks/stripe`
- Handle Stripe Webhook

`GET` `/`
- Root

## auth

`POST` `/api/v1/auth/token`
- Login For Access Token

`POST` `/api/v1/auth/refresh`
- Refresh Access Token

`POST` `/api/v1/auth/logout`
- Logout Session

`POST` `/api/v1/auth/logout/all`
- Logout All Sessions

`GET` `/api/v1/auth/sessions`
- List User Sessions

`DELETE` `/api/v1/auth/sessions/{session_id}`
- Revoke User Session

`GET` `/api/v1/auth/me`
- Get Current User Info

`POST` `/api/v1/auth/email/send`
- Send Email Verification

`POST` `/api/v1/auth/email/verify`
- Verify Email Token

`POST` `/api/v1/auth/password/forgot`
- Request Password Reset

`POST` `/api/v1/auth/password/confirm`
- Confirm Password Reset

`POST` `/api/v1/auth/password/change`
- Change Password

`POST` `/api/v1/auth/password/reset`
- Admin Reset Password

`POST` `/api/v1/auth/service-accounts/issue`
- Issue Service Account Token

`POST` `/api/v1/auth/service-accounts/browser-issue`
- Issue Service Account Token From Browser

`GET` `/api/v1/auth/service-accounts/tokens`
- List Service Account Tokens

`POST` `/api/v1/auth/service-accounts/tokens/{jti}/revoke`
- Revoke Service Account Token

`GET` `/api/v1/auth/signup-policy`
- Get Signup Access Policy

`POST` `/api/v1/auth/register`
- Register Tenant

`POST` `/api/v1/auth/request-access`
- Submit Access Request

`GET` `/api/v1/auth/signup-requests`
- List Signup Requests

`POST` `/api/v1/auth/signup-requests/{request_id}/approve`
- Approve Signup Request

`POST` `/api/v1/auth/signup-requests/{request_id}/reject`
- Reject Signup Request

`GET` `/api/v1/auth/invites`
- List Invites

`POST` `/api/v1/auth/invites`
- Issue Invite

`POST` `/api/v1/auth/invites/{invite_id}/revoke`
- Revoke Invite

## chat

`POST` `/api/v1/chat`
- Chat With Agent (body: message, optional conversation_id, agent_type, context, share_location, location)

`POST` `/api/v1/chat/stream`
- Stream Chat With Agent (same body as Chat; client-supplied run_options are not accepted)

## agents

`GET` `/api/v1/agents`
- List Available Agents

`GET` `/api/v1/agents/{agent_name}/status`
- Get Agent Status

## workflows

`GET` `/api/v1/workflows`
- List Workflows

`POST` `/api/v1/workflows/{workflow_key}/run`
- Run Workflow

`GET` `/api/v1/workflows/runs`
- List Workflow Runs

`GET` `/api/v1/workflows/runs/{run_id}`
- Get Workflow Run

`POST` `/api/v1/workflows/runs/{run_id}/cancel`
- Cancel Workflow Run

`POST` `/api/v1/workflows/{workflow_key}/run-stream`
- Run Workflow Stream

`GET` `/api/v1/workflows/{workflow_key}`
- Get Workflow Descriptor

## conversations

`GET` `/api/v1/conversations`
- List Conversations (returns agent_entrypoint, active_agent, topic_hint/title, status, message_count, last_message_preview, created_at, updated_at)

`GET` `/api/v1/conversations/search`
- Search Conversations (same fields as list plus preview/score)

`GET` `/api/v1/conversations/{conversation_id}`
- Get Conversation (messages plus agent_context populated with agent metadata)

`DELETE` `/api/v1/conversations/{conversation_id}`
- Delete Conversation

`GET` `/api/v1/conversations/{conversation_id}/events`
- Get Conversation Events

## tools

`GET` `/api/v1/tools`
- List Available Tools

## containers

`POST` `/api/v1/containers`
- Create Container

`GET` `/api/v1/containers`
- List Containers

`GET` `/api/v1/containers/{container_id}`
- Get Container By Id

`DELETE` `/api/v1/containers/{container_id}`
- Delete Container

`POST` `/api/v1/containers/agents/{agent_key}/container`
- Bind Agent Container

`DELETE` `/api/v1/containers/agents/{agent_key}/container`
- Unbind Agent Container

## vector-stores

`POST` `/api/v1/vector-stores`
- Create Vector Store

`GET` `/api/v1/vector-stores`
- List Vector Stores

`GET` `/api/v1/vector-stores/{vector_store_id}`
- Get Vector Store

`DELETE` `/api/v1/vector-stores/{vector_store_id}`
- Delete Vector Store

`POST` `/api/v1/vector-stores/{vector_store_id}/files`
- Attach File

`POST` `/api/v1/vector-stores/{vector_store_id}/files/upload`
- Upload Stored Object + Attach File (requires agent_key)

`GET` `/api/v1/vector-stores/{vector_store_id}/files`
- List Files

`GET` `/api/v1/vector-stores/{vector_store_id}/files/{file_id}`
- Get File

`DELETE` `/api/v1/vector-stores/{vector_store_id}/files/{file_id}`
- Delete File

`POST` `/api/v1/vector-stores/{vector_store_id}/search`
- Search Vector Store

## storage

`POST` `/api/v1/storage/objects/upload-url`
- Create Presigned Upload

`GET` `/api/v1/storage/objects`
- List Objects

`GET` `/api/v1/storage/objects/{object_id}/download-url`
- Get Download Url

`DELETE` `/api/v1/storage/objects/{object_id}`
- Delete Object

## contact

`POST` `/api/v1/contact`
- Submit Contact

## status

`GET` `/api/v1/status`
- Get Platform Status

`GET` `/api/v1/status/rss`
- Get Platform Status Rss

`POST` `/api/v1/status/subscriptions`
- Create Status Subscription

`GET` `/api/v1/status/subscriptions`
- List Status Subscriptions

`POST` `/api/v1/status/subscriptions/verify`
- Verify Status Subscription

`POST` `/api/v1/status/subscriptions/challenge`
- Confirm Webhook Challenge

`DELETE` `/api/v1/status/subscriptions/{subscription_id}`
- Revoke Status Subscription

`POST` `/api/v1/status/incidents/{incident_id}/resend`
- Resend Status Incident

`GET` `/api/v1/status.rss`
- Get Platform Status Rss Alias

## tenants

`GET` `/api/v1/tenants/settings`
- Get Tenant Settings

`PUT` `/api/v1/tenants/settings`
- Update Tenant Settings

## billing

`GET` `/api/v1/billing/plans`
- List Billing Plans

`GET` `/api/v1/billing/tenants/{tenant_id}/subscription`
- Get Tenant Subscription

`POST` `/api/v1/billing/tenants/{tenant_id}/subscription`
- Start Subscription

`PATCH` `/api/v1/billing/tenants/{tenant_id}/subscription`
- Update Subscription

`POST` `/api/v1/billing/tenants/{tenant_id}/subscription/cancel`
- Cancel Subscription

`POST` `/api/v1/billing/tenants/{tenant_id}/usage`
- Record Usage

`GET` `/api/v1/billing/tenants/{tenant_id}/events`
- List Billing Events

`GET` `/api/v1/billing/stream`
- Billing Event Stream

---

# Schemas

- `AgentChatRequest` (object)
- `AgentChatResponse` (object)
- `AgentStatus` (object)
- `AgentSummary` (object)
- `BillingContactModel` (object)
- `BillingEventHistoryResponse` (object)
- `BillingEventInvoiceResponse` (object)
- `BillingEventResponse` (object)
- `BillingEventSubscriptionResponse` (object)
- `BillingEventUsageResponse` (object)
- `BillingPlanResponse` (object)
- `BrowserServiceAccountIssueRequest` (object)
- `CancelSubscriptionRequest` (object)
- `ChatMessage` (object)
- `ContactSubmissionRequest` (object)
- `ContainerBindRequest` (object)
- `ContainerCreateRequest` (object)
- `ContainerListResponse` (object)
- `ContainerResponse` (object)
- `ConversationEventItem` (object)
- `ConversationEventsResponse` (object)
- `ConversationHistory` (object)
- `ConversationListResponse` (object)
- `ConversationSearchResponse` (object)
- `ConversationSearchResult` (object)
- `ConversationSummary` (object)
- `EmailVerificationConfirmRequest` (object)
- `HTTPValidationError` (object)
- `HealthResponse` (object)
- `IncidentSchema` (object)
- `LocationHint` (object)
- `MessageAttachment` (object)
- `PasswordChangeRequest` (object)
- `PasswordForgotRequest` (object)
- `PasswordResetConfirmRequest` (object)
- `PasswordResetRequest` (object)
- `PlanFeatureResponse` (object)
- `PlatformStatusResponse` (object)
- `RunOptionsRequest` (object)
- `ServiceAccountIssueRequest` (object)
- `ServiceAccountTokenItem` (object)
- `ServiceAccountTokenListResponse` (object)
- `ServiceAccountTokenResponse` (object)
- `ServiceAccountTokenRevokeRequest` (object)
- `ServiceAccountTokenStatus` (string)
- `ServiceStatusSchema` (object)
- `SessionClientInfo` (object)
- `SessionLocationInfo` (object)
- `SignupAccessPolicyResponse` (object)
- `SignupInviteIssueRequest` (object)
- `SignupInviteIssueResponse` (object)
- `SignupInviteListResponse` (object)
- `SignupInviteResponse` (object)
- `SignupInviteStatus` (string)
- `SignupRequestApprovalRequest` (object)
- `SignupRequestDecisionResponse` (object)
- `SignupRequestListResponse` (object)
- `SignupRequestPublicRequest` (object)
- `SignupRequestRejectionRequest` (object)
- `SignupRequestResponse` (object)
- `SignupRequestStatus` (string)
- `StartSubscriptionRequest` (object)
- `StatusIncidentResendRequest` (object)
- `StatusIncidentResendResponse` (object)
- `StatusOverviewSchema` (object)
- `StatusSubscriptionChallengeRequest` (object)
- `StatusSubscriptionCreateRequest` (object)
- `StatusSubscriptionListResponse` (object)
- `StatusSubscriptionResponse` (object)
- `StatusSubscriptionVerifyRequest` (object)
- `StorageObjectListResponse` (object)
- `StorageObjectResponse` (object)
- `StoragePresignDownloadResponse` (object)
- `StoragePresignUploadRequest` (object)
- `StoragePresignUploadResponse` (object)
- `StreamingChatEvent` (object)
- `StreamingWorkflowEvent` (object)

Streaming event notes:
- `run_item_type` is the semantic classification (`user_message`, `assistant_message`, `tool_call`, `tool_result`, etc.). We also emit lifecycle `memory_compaction` events (`kind=response.memory.compacted`, `run_item_type=memory_compaction`) when a compact strategy rewrites the SDK session. Payload keys include `compacted_count`, `compacted_call_ids`, `compacted_tool_names`, `keep_turns`, `trigger_turns`, `clear_tool_inputs`, `excluded_tools`, `total_items_before/after`, `turns_before/after`. Clients may safely ignore unknown kinds.
- `StripeEventStatus` (string)
- `SuccessResponse` (object)
- `TenantSettingsResponse` (object)
- `TenantSettingsUpdateRequest` (object)
- `TenantSubscriptionResponse` (object)
- `UpdateSubscriptionRequest` (object)
- `UptimeMetricSchema` (object)
- `UsageRecordRequest` (object)
- `UserLoginRequest` (object)
- `UserLogoutRequest` (object)
- `UserRefreshRequest` (object)
- `UserRegisterRequest` (object)
- `UserRegisterResponse` (object)
- `UserSessionItem` (object)
- `UserSessionListResponse` (object)
- `UserSessionResponse` (object)
- `ValidationError` (object)
- `VectorStoreCreateRequest` (object)
- `VectorStoreFileCreateRequest` (object)
- `VectorStoreFileListResponse` (object)
- `VectorStoreFileResponse` (object)
- `VectorStoreListResponse` (object)
- `VectorStoreResponse` (object)
- `VectorStoreSearchRequest` (object)
- `VectorStoreSearchResponse` (object)
- `WorkflowDescriptorResponse` (object)
- `WorkflowRunDetail` (object)
- `WorkflowRunListItem` (object)
- `WorkflowRunListResponse` (object)
- `WorkflowRunRequestBody` (object)
- `WorkflowRunResponse` (object)
- `WorkflowStageDescriptor` (object)
- `WorkflowStepDescriptor` (object)
- `WorkflowStepResultSchema` (object)
- `WorkflowSummary` (object)

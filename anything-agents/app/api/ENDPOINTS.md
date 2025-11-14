Of course. Here is the documentation formatted in a clean, readable Markdown format.

***

## Health

- `GET` `/health` - Health Check
- `GET` `/health/ready` - Readiness Check

## Default

- `POST` `/webhooks/stripe` - Handle Stripe Webhook
- `GET` `/` - Root

## Auth

- `POST` `/api/v1/auth/token` - Login For Access Token
- `POST` `/api/v1/auth/refresh` - Refresh Access Token
- `POST` `/api/v1/auth/logout` - Logout Session
- `POST` `/api/v1/auth/logout/all` - Logout All Sessions
- `GET` `/api/v1/auth/sessions` - List User Sessions
- `DELETE` `/api/v1/auth/sessions/{session_id}` - Revoke User Session
- `GET` `/api/v1/auth/me` - Get Current User Info
- `POST` `/api/v1/auth/email/send` - Send Email Verification
- `POST` `/api/v1/auth/email/verify` - Verify Email Token
- `POST` `/api/v1/auth/password/forgot` - Request Password Reset
- `POST` `/api/v1/auth/password/confirm` - Confirm Password Reset
- `POST` `/api/v1/auth/password/change` - Change Password
- `POST` `/api/v1/auth/password/reset` - Admin Reset Password
- `POST` `/api/v1/auth/service-accounts/issue` - Issue Service Account Token
- `POST` `/api/v1/auth/register` - Register Tenant

## Chat

- `POST` `/api/v1/chat` - Chat With Agent
- `POST` `/api/v1/chat/stream` - Stream Chat With Agent

## Agents

- `GET` `/api/v1/agents` - List Available Agents
- `GET` `/api/v1/agents/{agent_name}/status` - Get Agent Status

## Conversations

- `GET` `/api/v1/conversations` - List Conversations
- `GET` `/api/v1/conversations/{conversation_id}` - Get Conversation
- `DELETE` `/api/v1/conversations/{conversation_id}` - Delete Conversation

## Tools

- `GET` `/api/v1/tools` - List Available Tools

## Billing

- `GET` `/api/v1/billing/plans` - List Billing Plans
- `GET` `/api/v1/billing/tenants/{tenant_id}/subscription` - Get Tenant Subscription
- `POST` `/api/v1/billing/tenants/{tenant_id}/subscription` - Start Subscription
- `PATCH` `/api/v1/billing/tenants/{tenant_id}/subscription` - Update Subscription
- `POST` `/api/v1/billing/tenants/{tenant_id}/subscription/cancel` - Cancel Subscription
- `POST` `/api/v1/billing/tenants/{tenant_id}/usage` - Record Usage
- `GET` `/api/v1/billing/stream` - Billing Event Stream

## Schemas

- `AgentChatRequest`
- `AgentChatResponse`
- `AgentStatus`
- `AgentSummary`
- `BillingPlanResponse`
- `CancelSubscriptionRequest`
- `ChatMessage`
- `ConversationHistory`
- `ConversationSummary`
- `EmailVerificationConfirmRequest`
- `HTTPValidationError`
- `HealthResponse`
- `PasswordChangeRequest`
- `PasswordForgotRequest`
- `PasswordResetConfirmRequest`
- `PasswordResetRequest`
- `PlanFeatureResponse`
- `ServiceAccountIssueRequest`
- `ServiceAccountTokenResponse`
- `SessionClientInfo`
- `SessionLocationInfo`
- `StartSubscriptionRequest`
- `SuccessResponse`
- `TenantSubscriptionResponse`
- `UpdateSubscriptionRequest`
- `UsageRecordRequest`
- `UserLoginRequest`
- `UserLogoutRequest`
- `UserRefreshRequest`
- `UserRegisterRequest`
- `UserRegisterResponse`
- `UserSessionItem`
- `UserSessionListResponse`
- `UserSessionResponse`
- `ValidationError`
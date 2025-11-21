# FastAPI Microservice API

## Health

### Health Check
```
GET /health
```

### Readiness Check
```
GET /health/ready
```

---

## Default

### Handle Stripe Webhook
```
POST /webhooks/stripe
```

### Root
```
GET /
```

---

## Auth

### Login For Access Token
```
POST /api/v1/auth/token
```

### Refresh Access Token
```
POST /api/v1/auth/refresh
```

### Logout Session
```
POST /api/v1/auth/logout
```

### Logout All Sessions
```
POST /api/v1/auth/logout/all
```

### List User Sessions
```
GET /api/v1/auth/sessions
```

### Revoke User Session
```
DELETE /api/v1/auth/sessions/{session_id}
```

### Get Current User Info
```
GET /api/v1/auth/me
```

### Send Email Verification
```
POST /api/v1/auth/email/send
```

### Verify Email Token
```
POST /api/v1/auth/email/verify
```

### Request Password Reset
```
POST /api/v1/auth/password/forgot
```

### Confirm Password Reset
```
POST /api/v1/auth/password/confirm
```

### Change Password
```
POST /api/v1/auth/password/change
```

### Admin Reset Password
```
POST /api/v1/auth/password/reset   # Backend contract; frontend proxies via /api/auth/password/admin-reset.
```

### Issue Service Account Token
```
POST /api/v1/auth/service-accounts/issue
```

### Issue Service Account Token From Browser
```
POST /api/v1/auth/service-accounts/browser-issue
```

### List Service Account Tokens
```
GET /api/v1/auth/service-accounts/tokens
```

### Revoke Service Account Token
```
POST /api/v1/auth/service-accounts/tokens/{jti}/revoke
```

### Get Signup Access Policy
```
GET /api/v1/auth/signup-policy
```

### Register Tenant
```
POST /api/v1/auth/register
```

### Submit Access Request
```
POST /api/v1/auth/request-access
```

### List Signup Requests
```
GET /api/v1/auth/signup-requests
```

### Approve Signup Request
```
POST /api/v1/auth/signup-requests/{request_id}/approve
```

### Reject Signup Request
```
POST /api/v1/auth/signup-requests/{request_id}/reject
```

### List Invites
```
GET /api/v1/auth/invites
```

### Issue Invite
```
POST /api/v1/auth/invites
```

### Revoke Invite
```
POST /api/v1/auth/invites/{invite_id}/revoke
```

---

## Chat

### Chat With Agent
```
POST /api/v1/chat
```

### Stream Chat With Agent
```
POST /api/v1/chat/stream
```

---

## Agents

### List Available Agents
```
GET /api/v1/agents
```

### Get Agent Status
```
GET /api/v1/agents/{agent_name}/status
```

---

## Conversations

### List Conversations
```
GET /api/v1/conversations
```

### Get Conversation
```
GET /api/v1/conversations/{conversation_id}
```

### Delete Conversation
```
DELETE /api/v1/conversations/{conversation_id}
```

---

## Tools

### List Available Tools
```
GET /api/v1/tools
```

---

## Status

### Get Platform Status
```
GET /api/v1/status
```

### Get Platform Status Rss
```
GET /api/v1/status/rss
```

### Create Status Subscription
```
POST /api/v1/status/subscriptions
```

### List Status Subscriptions
```
GET /api/v1/status/subscriptions
```

### Verify Status Subscription
```
POST /api/v1/status/subscriptions/verify
```

### Confirm Webhook Challenge
```
POST /api/v1/status/subscriptions/challenge
```

### Revoke Status Subscription
```
DELETE /api/v1/status/subscriptions/{subscription_id}
```

### Resend Status Incident
```
POST /api/v1/status/incidents/{incident_id}/resend
```

### Get Platform Status Rss Alias
```
GET /api/v1/status.rss
```

---

## Tenants

### Get Tenant Settings
```
GET /api/v1/tenants/settings
```

### Update Tenant Settings
```
PUT /api/v1/tenants/settings
```

---

## Billing

### List Billing Plans
```
GET /api/v1/billing/plans
```

### Get Tenant Subscription
```
GET /api/v1/billing/tenants/{tenant_id}/subscription
```

### Start Subscription
```
POST /api/v1/billing/tenants/{tenant_id}/subscription
```

### Update Subscription
```
PATCH /api/v1/billing/tenants/{tenant_id}/subscription
```

### Cancel Subscription
```
POST /api/v1/billing/tenants/{tenant_id}/subscription/cancel
```

### Record Usage
```
POST /api/v1/billing/tenants/{tenant_id}/usage
```

### List Billing Events
```
GET /api/v1/billing/tenants/{tenant_id}/events
```

### Billing Event Stream
```
GET /api/v1/billing/stream
```

---

## Schemas

*   AgentChatRequest
*   AgentChatResponse
*   AgentStatus
*   AgentSummary
*   BillingContactModel
*   BillingEventHistoryResponse
*   BillingEventInvoiceResponse
*   BillingEventResponse
*   BillingEventSubscriptionResponse
*   BillingEventUsageResponse
*   BillingPlanResponse
*   BrowserServiceAccountIssueRequest
*   CancelSubscriptionRequest
*   ChatMessage
*   ConversationHistory
*   ConversationSummary
*   EmailVerificationConfirmRequest
*   HTTPValidationError
*   HealthResponse
*   IncidentSchema
*   PasswordChangeRequest
*   PasswordForgotRequest
*   PasswordResetConfirmRequest
*   PasswordResetRequest
*   PlanFeatureResponse
*   PlatformStatusResponse
*   ServiceAccountIssueRequest
*   ServiceAccountTokenItem
*   ServiceAccountTokenListResponse
*   ServiceAccountTokenResponse
*   ServiceAccountTokenRevokeRequest
*   ServiceAccountTokenStatus
*   ServiceStatusSchema
*   SessionClientInfo
*   SessionLocationInfo
*   SignupAccessPolicyResponse
*   SignupInviteIssueRequest
*   SignupInviteIssueResponse
*   SignupInviteListResponse
*   SignupInviteResponse
*   SignupInviteStatus
*   SignupRequestApprovalRequest
*   SignupRequestDecisionResponse
*   SignupRequestListResponse
*   SignupRequestPublicRequest
*   SignupRequestRejectionRequest
*   SignupRequestResponse
*   SignupRequestStatus
*   StartSubscriptionRequest
*   StatusIncidentResendRequest
*   StatusIncidentResendResponse
*   StatusOverviewSchema
*   StatusSubscriptionChallengeRequest
*   StatusSubscriptionCreateRequest
*   StatusSubscriptionListResponse
*   StatusSubscriptionResponse
*   StatusSubscriptionVerifyRequest
*   StripeEventStatus
*   SuccessResponse
*   TenantSettingsResponse
*   TenantSettingsUpdateRequest
*   TenantSubscriptionResponse
*   UpdateSubscriptionRequest
*   UptimeMetricSchema
*   UsageRecordRequest
*   UserLoginRequest
*   UserLogoutRequest
*   UserRefreshRequest
*   UserRegisterRequest
*   UserRegisterResponse
*   UserSessionItem
*   UserSessionListResponse
*   UserSessionResponse
*   ValidationError

# API Service

# Health

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health Check |
| `GET` | `/health/ready` | Readiness Check |
| `GET` | `/health/storage` | Storage Health |

# Default

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/webhooks/stripe` | Handle Stripe Webhook |
| `GET` | `/` | Root |

# Auth

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/token` | Login For Access Token |
| `POST` | `/api/v1/auth/refresh` | Refresh Access Token |
| `POST` | `/api/v1/auth/logout` | Logout Session |
| `POST` | `/api/v1/auth/logout/all` | Logout All Sessions |
| `GET` | `/api/v1/auth/sessions` | List User Sessions |
| `DELETE` | `/api/v1/auth/sessions/{session_id}` | Revoke User Session |
| `GET` | `/api/v1/auth/me` | Get Current User Info |
| `POST` | `/api/v1/auth/email/send` | Send Email Verification |
| `POST` | `/api/v1/auth/email/verify` | Verify Email Token |
| `POST` | `/api/v1/auth/password/forgot` | Request Password Reset |
| `POST` | `/api/v1/auth/password/confirm` | Confirm Password Reset |
| `POST` | `/api/v1/auth/password/change` | Change Password |
| `POST` | `/api/v1/auth/password/reset` | Admin Reset Password |
| `POST` | `/api/v1/auth/service-accounts/issue` | Issue Service Account Token |
| `POST` | `/api/v1/auth/service-accounts/browser-issue` | Issue Service Account Token From Browser |
| `GET` | `/api/v1/auth/service-accounts/tokens` | List Service Account Tokens |
| `POST` | `/api/v1/auth/service-accounts/tokens/{jti}/revoke` | Revoke Service Account Token |
| `GET` | `/api/v1/auth/signup-policy` | Get Signup Access Policy |
| `POST` | `/api/v1/auth/register` | Register Tenant |
| `POST` | `/api/v1/auth/request-access` | Submit Access Request |
| `GET` | `/api/v1/auth/signup-requests` | List Signup Requests |
| `POST` | `/api/v1/auth/signup-requests/{request_id}/approve` | Approve Signup Request |
| `POST` | `/api/v1/auth/signup-requests/{request_id}/reject` | Reject Signup Request |
| `GET` | `/api/v1/auth/invites` | List Invites |
| `POST` | `/api/v1/auth/invites` | Issue Invite |
| `POST` | `/api/v1/auth/invites/{invite_id}/revoke` | Revoke Invite |

# Chat

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/chat` | Chat With Agent |
| `POST` | `/api/v1/chat/stream` | Stream Chat With Agent |

# Agents

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/agents` | List Available Agents |
| `GET` | `/api/v1/agents/{agent_name}/status` | Get Agent Status |

# Workflows

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/workflows` | List Workflows |
| `POST` | `/api/v1/workflows/{workflow_key}/run` | Run Workflow |
| `GET` | `/api/v1/workflows/runs` | List Workflow Runs |
| `GET` | `/api/v1/workflows/runs/{run_id}` | Get Workflow Run |
| `POST` | `/api/v1/workflows/runs/{run_id}/cancel` | Cancel Workflow Run |
| `POST` | `/api/v1/workflows/{workflow_key}/run-stream` | Run Workflow Stream |
| `GET` | `/api/v1/workflows/{workflow_key}` | Get Workflow Descriptor |

# Conversations

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/conversations` | List Conversations |
| `GET` | `/api/v1/conversations/search` | Search Conversations |
| `GET` | `/api/v1/conversations/{conversation_id}` | Get Conversation |
| `DELETE` | `/api/v1/conversations/{conversation_id}` | Delete Conversation |
| `GET` | `/api/v1/conversations/{conversation_id}/events` | Get Conversation Events |

# Tools

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/tools` | List Available Tools |

# Containers

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/containers` | Create Container |
| `GET` | `/api/v1/containers` | List Containers |
| `GET` | `/api/v1/containers/{container_id}` | Get Container By Id |
| `DELETE` | `/api/v1/containers/{container_id}` | Delete Container |
| `POST` | `/api/v1/containers/agents/{agent_key}/container` | Bind Agent Container |
| `DELETE` | `/api/v1/containers/agents/{agent_key}/container` | Unbind Agent Container |

# Vector-stores

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/vector-stores` | Create Vector Store |
| `GET` | `/api/v1/vector-stores` | List Vector Stores |
| `GET` | `/api/v1/vector-stores/{vector_store_id}` | Get Vector Store |
| `DELETE` | `/api/v1/vector-stores/{vector_store_id}` | Delete Vector Store |
| `POST` | `/api/v1/vector-stores/{vector_store_id}/files` | Attach File |
| `GET` | `/api/v1/vector-stores/{vector_store_id}/files` | List Files |
| `GET` | `/api/v1/vector-stores/{vector_store_id}/files/{file_id}` | Get File |
| `DELETE` | `/api/v1/vector-stores/{vector_store_id}/files/{file_id}` | Delete File |
| `POST` | `/api/v1/vector-stores/{vector_store_id}/search` | Search Vector Store |

# Storage

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/storage/objects/upload-url` | Create Presigned Upload |
| `GET` | `/api/v1/storage/objects` | List Objects |
| `GET` | `/api/v1/storage/objects/{object_id}/download-url` | Get Download Url |
| `DELETE` | `/api/v1/storage/objects/{object_id}` | Delete Object |

# Contact

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/contact` | Submit Contact |

# Status

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/status` | Get Platform Status |
| `GET` | `/api/v1/status/rss` | Get Platform Status Rss |
| `POST` | `/api/v1/status/subscriptions` | Create Status Subscription |
| `GET` | `/api/v1/status/subscriptions` | List Status Subscriptions |
| `POST` | `/api/v1/status/subscriptions/verify` | Verify Status Subscription |
| `POST` | `/api/v1/status/subscriptions/challenge` | Confirm Webhook Challenge |
| `DELETE` | `/api/v1/status/subscriptions/{subscription_id}` | Revoke Status Subscription |
| `POST` | `/api/v1/status/incidents/{incident_id}/resend` | Resend Status Incident |
| `GET` | `/api/v1/status.rss` | Get Platform Status Rss Alias |

# Tenants

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/tenants/settings` | Get Tenant Settings |
| `PUT` | `/api/v1/tenants/settings` | Update Tenant Settings |

# Billing

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/billing/plans` | List Billing Plans |
| `GET` | `/api/v1/billing/tenants/{tenant_id}/subscription` | Get Tenant Subscription |
| `POST` | `/api/v1/billing/tenants/{tenant_id}/subscription` | Start Subscription |
| `PATCH` | `/api/v1/billing/tenants/{tenant_id}/subscription` | Update Subscription |
| `POST` | `/api/v1/billing/tenants/{tenant_id}/subscription/cancel` | Cancel Subscription |
| `POST` | `/api/v1/billing/tenants/{tenant_id}/usage` | Record Usage |
| `GET` | `/api/v1/billing/tenants/{tenant_id}/events` | List Billing Events |
| `GET` | `/api/v1/billing/stream` | Billing Event Stream |

# Schemas

* `AgentChatRequestExpand allobject`
* `AgentChatResponseExpand allobject`
* `AgentStatusExpand allobject`
* `AgentSummaryExpand allobject`
* `BillingContactModelExpand allobject`
* `BillingEventHistoryResponseExpand allobject`
* `BillingEventInvoiceResponseExpand allobject`
* `BillingEventResponseExpand allobject`
* `BillingEventSubscriptionResponseExpand allobject`
* `BillingEventUsageResponseExpand allobject`
* `BillingPlanResponseExpand allobject`
* `BrowserServiceAccountIssueRequestExpand allobject`
* `CancelSubscriptionRequestExpand allobject`
* `ChatMessageExpand allobject`
* `ContactSubmissionRequestExpand allobject`
* `ContainerBindRequestExpand allobject`
* `ContainerCreateRequestExpand allobject`
* `ContainerListResponseExpand allobject`
* `ContainerResponseExpand allobject`
* `ConversationEventItemExpand allobject`
* `ConversationEventsResponseExpand allobject`
* `ConversationHistoryExpand allobject`
* `ConversationListResponseExpand allobject`
* `ConversationSearchResponseExpand allobject`
* `ConversationSearchResultExpand allobject`
* `ConversationSummaryExpand allobject`
* `EmailVerificationConfirmRequestExpand allobject`
* `HTTPValidationErrorExpand allobject`
* `HealthResponseExpand allobject`
* `IncidentSchemaExpand allobject`
* `LocationHintExpand allobject`
* `MessageAttachmentExpand allobject`
* `PasswordChangeRequestExpand allobject`
* `PasswordForgotRequestExpand allobject`
* `PasswordResetConfirmRequestExpand allobject`
* `PasswordResetRequestExpand allobject`
* `PlanFeatureResponseExpand allobject`
* `PlatformStatusResponseExpand allobject`
* `RunOptionsRequestExpand allobject`
* `ServiceAccountIssueRequestExpand allobject`
* `ServiceAccountTokenItemExpand allobject`
* `ServiceAccountTokenListResponseExpand allobject`
* `ServiceAccountTokenResponseExpand allobject`
* `ServiceAccountTokenRevokeRequestExpand allobject`
* `ServiceAccountTokenStatusExpand allstring`
* `ServiceStatusSchemaExpand allobject`
* `SessionClientInfoExpand allobject`
* `SessionLocationInfoExpand allobject`
* `SignupAccessPolicyResponseExpand allobject`
* `SignupInviteIssueRequestExpand allobject`
* `SignupInviteIssueResponseExpand allobject`
* `SignupInviteListResponseExpand allobject`
* `SignupInviteResponseExpand allobject`
* `SignupInviteStatusExpand allstring`
* `SignupRequestApprovalRequestExpand allobject`
* `SignupRequestDecisionResponseExpand allobject`
* `SignupRequestListResponseExpand allobject`
* `SignupRequestPublicRequestExpand allobject`
* `SignupRequestRejectionRequestExpand allobject`
* `SignupRequestResponseExpand allobject`
* `SignupRequestStatusExpand allstring`
* `StartSubscriptionRequestExpand allobject`
* `StatusIncidentResendRequestExpand allobject`
* `StatusIncidentResendResponseExpand allobject`
* `StatusOverviewSchemaExpand allobject`
* `StatusSubscriptionChallengeRequestExpand allobject`
* `StatusSubscriptionCreateRequestExpand allobject`
* `StatusSubscriptionListResponseExpand allobject`
* `StatusSubscriptionResponseExpand allobject`
* `StatusSubscriptionVerifyRequestExpand allobject`
* `StorageObjectListResponseExpand allobject`
* `StorageObjectResponseExpand allobject`
* `StoragePresignDownloadResponseExpand allobject`
* `StoragePresignUploadRequestExpand allobject`
* `StoragePresignUploadResponseExpand allobject`
* `StreamingChatEventExpand allobject`
* `StreamingWorkflowEventExpand allobject`
* `StripeEventStatusExpand allstring`
* `SuccessResponseExpand allobject`
* `TenantSettingsResponseExpand allobject`
* `TenantSettingsUpdateRequestExpand allobject`
* `TenantSubscriptionResponseExpand allobject`
* `UpdateSubscriptionRequestExpand allobject`
* `UptimeMetricSchemaExpand allobject`
* `UsageRecordRequestExpand allobject`
* `UserLoginRequestExpand allobject`
* `UserLogoutRequestExpand allobject`
* `UserRefreshRequestExpand allobject`
* `UserRegisterRequestExpand allobject`
* `UserRegisterResponseExpand allobject`
* `UserSessionItemExpand allobject`
* `UserSessionListResponseExpand allobject`
* `UserSessionResponseExpand allobject`
* `ValidationErrorExpand allobject`
* `VectorStoreCreateRequestExpand allobject`
* `VectorStoreFileCreateRequestExpand allobject`
* `VectorStoreFileListResponseExpand allobject`
* `VectorStoreFileResponseExpand allobject`
* `VectorStoreListResponseExpand allobject`
* `VectorStoreResponseExpand allobject`
* `VectorStoreSearchRequestExpand allobject`
* `VectorStoreSearchResponseExpand allobject`
* `WorkflowDescriptorResponseExpand allobject`
* `WorkflowRunDetailExpand allobject`
* `WorkflowRunListItemExpand allobject`
* `WorkflowRunListResponseExpand allobject`
* `WorkflowRunRequestBodyExpand allobject`
* `WorkflowRunResponseExpand allobject`
* `WorkflowStageDescriptorExpand allobject`
* `WorkflowStepDescriptorExpand allobject`
* `WorkflowStepResultSchemaExpand allobject`
* `WorkflowSummaryExpand allobject`
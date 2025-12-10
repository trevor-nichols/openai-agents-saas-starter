import type { SignupAccessPolicy, SignupInviteSummary, SignupRequestSummary } from '@/types/signup';

const now = Date.now();

export const samplePolicy: SignupAccessPolicy = {
  policy: 'invite_only',
  invite_required: true,
  request_access_enabled: true,
};

export const sampleInvite: SignupInviteSummary = {
  id: 'invite-story',
  tokenHint: 'story-1234',
  invitedEmail: 'user@example.com',
  status: 'active',
  maxRedemptions: 3,
  redeemedCount: 1,
  expiresAt: new Date(now + 48 * 60 * 60 * 1000).toISOString(),
  createdAt: new Date(now - 60 * 60 * 1000).toISOString(),
  signupRequestId: 'req-story',
  note: 'Storybook sample',
};

export const sampleRequest: SignupRequestSummary = {
  id: 'req-story',
  email: 'prospect@example.com',
  organization: 'Storybook Inc',
  fullName: 'Terry Example',
  status: 'pending',
  createdAt: new Date(now - 2 * 60 * 60 * 1000).toISOString(),
  decisionReason: null,
  inviteTokenHint: null,
};

import type { SignupAccessPolicy } from '@/types/signup';
import type { MfaChallengeResponse } from '@/lib/api/client/types.gen';

export const authPolicyInviteOnly: SignupAccessPolicy = {
  policy: 'invite_only',
  invite_required: true,
  request_access_enabled: true,
};

export const authPolicyPublic: SignupAccessPolicy = {
  policy: 'public',
  invite_required: false,
  request_access_enabled: false,
};

export const authMfaChallenge: MfaChallengeResponse = {
  challenge_token: 'mfa_tok_123',
  methods: [
    { id: 'totp-1', method_type: 'totp', label: 'Authenticator App' },
    { id: 'sms-1', method_type: 'sms', label: 'SMS to ••••1234' },
  ],
};
